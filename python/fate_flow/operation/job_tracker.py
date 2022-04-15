#
#  Copyright 2019 The FATE Authors. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
import operator
import copy
import typing

from fate_arch.abc import CTableABC
from fate_arch.common import EngineType, Party
from fate_arch.common.data_utils import default_output_fs_path, default_output_info
from fate_arch.computing import ComputingEngine
from fate_arch.federation import FederationEngine
from fate_arch.storage import StorageEngine
from fate_arch.common.base_utils import current_timestamp, serialize_b64, deserialize_b64, json_loads
from fate_flow.utils.log_utils import schedule_logger
from fate_flow.db.db_models import (DB, Job, TrackingOutputDataInfo,
                                    ComponentSummary, MachineLearningModelInfo as MLModel)
from fate_flow.entity import Metric, MetricMeta
from fate_flow.entity import DataCache
from fate_flow.db.runtime_config import RuntimeConfig
from fate_flow.db.job_default_config import JobDefaultConfig
from fate_flow.pipelined_model import pipelined_model
from fate_flow.manager.cache_manager import CacheManager
from fate_flow.manager.metric_manager import MetricManager
from fate_arch import storage, session
from fate_flow.utils import model_utils, job_utils, data_utils
from fate_flow.entity import RunParameters


class Tracker(object):
    """
    Tracker for Job/Task/Metric
    """
    METRIC_DATA_PARTITION = 48
    METRIC_LIST_PARTITION = 48
    JOB_VIEW_PARTITION = 8

    def __init__(self, job_id: str, role: str, party_id: int,
                 model_id: str = None,
                 model_version: str = None,
                 component_name: str = None,
                 component_module_name: str = None,
                 task_id: str = None,
                 task_version: int = None,
                 job_parameters: RunParameters = None
                 ):
        self.job_id = job_id
        self.job_parameters = job_parameters
        self.role = role
        self.party_id = party_id
        self.component_name = component_name if component_name else job_utils.job_pipeline_component_name()
        self.module_name = component_module_name if component_module_name else job_utils.job_pipeline_component_module_name()
        self.task_id = task_id
        self.task_version = task_version

        self.model_id = model_id
        self.party_model_id = model_utils.gen_party_model_id(model_id=model_id, role=role, party_id=party_id)
        self.model_version = model_version
        self.pipelined_model = None
        if self.party_model_id and self.model_version:
            self.pipelined_model = pipelined_model.PipelinedModel(model_id=self.party_model_id,
                                                                  model_version=self.model_version)
        self.metric_manager = MetricManager(job_id=self.job_id, role=self.role, party_id=self.party_id, component_name=self.component_name, task_id=self.task_id, task_version=self.task_version)

    def save_metric_data(self, metric_namespace: str, metric_name: str, metrics: typing.List[Metric], job_level=False):
        schedule_logger(self.job_id).info(
            'save component {} on {} {} {} {} metric data'.format(self.component_name, self.role,
                                                                  self.party_id, metric_namespace, metric_name))
        kv = []
        for metric in metrics:
            kv.append((metric.key, metric.value))
        self.metric_manager.insert_metrics_into_db(metric_namespace, metric_name, 1, kv, job_level)

    def get_job_metric_data(self, metric_namespace: str, metric_name: str):
        return self.read_metric_data(metric_namespace=metric_namespace, metric_name=metric_name, job_level=True)

    def get_metric_data(self, metric_namespace: str, metric_name: str):
        return self.read_metric_data(metric_namespace=metric_namespace, metric_name=metric_name, job_level=False)

    @DB.connection_context()
    def read_metric_data(self, metric_namespace: str, metric_name: str, job_level=False):
        metrics = []
        for k, v in self.metric_manager.read_metrics_from_db(metric_namespace, metric_name, 1, job_level):
            metrics.append(Metric(key=k, value=v))
        return metrics

    def save_metric_meta(self, metric_namespace: str, metric_name: str, metric_meta: MetricMeta,
                         job_level: bool = False):
        schedule_logger(self.job_id).info(
            'save component {} on {} {} {} {} metric meta'.format(self.component_name, self.role,
                                                                  self.party_id, metric_namespace, metric_name))
        self.metric_manager.insert_metrics_into_db(metric_namespace, metric_name, 0, metric_meta.to_dict().items(), job_level)

    @DB.connection_context()
    def get_metric_meta(self, metric_namespace: str, metric_name: str, job_level: bool = False):
        kv = dict()
        for k, v in self.metric_manager.read_metrics_from_db(metric_namespace, metric_name, 0, job_level):
            kv[k] = v
        return MetricMeta(name=kv.get('name'), metric_type=kv.get('metric_type'), extra_metas=kv)

    def log_job_view(self, view_data: dict):
        self.metric_manager.insert_metrics_into_db('job', 'job_view', 2, view_data.items(), job_level=True)

    @DB.connection_context()
    def get_job_view(self):
        view_data = {}
        for k, v in self.metric_manager.read_metrics_from_db('job', 'job_view', 2, job_level=True):
            view_data[k] = v
        return view_data

    def save_output_data(self, computing_table, output_storage_engine, output_storage_address=None,
                         output_table_namespace=None, output_table_name=None, schema=None, token=None, need_read=True):
        if computing_table:
            if not output_table_namespace or not output_table_name:
                output_table_namespace, output_table_name = default_output_info(task_id=self.task_id, task_version=self.task_version, output_type="data")
            schedule_logger(self.job_id).info(
                'persisting the component output temporary table to {} {}'.format(output_table_namespace,
                                                                                  output_table_name))

            part_of_limit = JobDefaultConfig.output_data_summary_count_limit
            part_of_data = []
            if need_read:
                match_id_name = computing_table.schema.get("match_id_name")
                schedule_logger(self.job_id).info(f'match id name:{match_id_name}')
                for k, v in computing_table.collect():
                    part_of_data.append((k, v))
                    part_of_limit -= 1
                    if part_of_limit == 0:
                        break

            session.Session.persistent(computing_table=computing_table,
                                       namespace=output_table_namespace,
                                       name=output_table_name,
                                       schema=schema,
                                       part_of_data=part_of_data,
                                       engine=output_storage_engine,
                                       engine_address=output_storage_address,
                                       token=token)

            return output_table_namespace, output_table_name
        else:
            schedule_logger(self.job_id).info('task id {} output data table is none'.format(self.task_id))
            return None, None

    def save_table_meta(self, meta):
        schedule_logger(self.job_id).info(f'start save table meta:{meta}')
        address = storage.StorageTableMeta.create_address(storage_engine=meta.get("engine"),
                                                          address_dict=meta.get("address"))
        table_meta = storage.StorageTableMeta(name=meta.get("name"), namespace=meta.get("namespace"), new=True)
        table_meta.set_metas(**meta)
        meta["address"] = address
        meta["part_of_data"] = deserialize_b64(meta["part_of_data"])
        meta["schema"] = deserialize_b64(meta["schema"])
        table_meta.create()
        schedule_logger(self.job_id).info(f'save table meta success')

    def get_table_meta(self, table_info):
        schedule_logger(self.job_id).info(f'start get table meta:{table_info}')
        table_meta_dict = storage.StorageTableMeta(namespace=table_info.get("namespace"), name=table_info.get("table_name"), create_address=False).to_dict()
        schedule_logger(self.job_id).info(f'get table meta success: {table_meta_dict}')
        table_meta_dict["part_of_data"] = serialize_b64(table_meta_dict["part_of_data"], to_str=True)
        table_meta_dict["schema"] = serialize_b64(table_meta_dict["schema"], to_str=True)
        return table_meta_dict

    def get_output_data_table(self, output_data_infos, tracker_client=None):
        """
        Get component output data table, will run in the task executor process
        :param output_data_infos:
        :return:
        """
        output_tables_meta = {}
        if output_data_infos:
            for output_data_info in output_data_infos:
                schedule_logger(self.job_id).info("get task {} {} output table {} {}".format(output_data_info.f_task_id, output_data_info.f_task_version, output_data_info.f_table_namespace, output_data_info.f_table_name))
                if not tracker_client:
                    data_table_meta = storage.StorageTableMeta(name=output_data_info.f_table_name, namespace=output_data_info.f_table_namespace)
                else:
                    data_table_meta = tracker_client.get_table_meta(output_data_info.f_table_name, output_data_info.f_table_namespace)

                output_tables_meta[output_data_info.f_data_name] = data_table_meta
        return output_tables_meta

    def init_pipeline_model(self):
        self.pipelined_model.create_pipelined_model()

    def save_output_model(self, model_buffers: dict, model_alias: str):
        if model_buffers:
            self.pipelined_model.save_component_model(component_name=self.component_name,
                                                      component_module_name=self.module_name,
                                                      model_alias=model_alias,
                                                      model_buffers=model_buffers)

    def get_output_model(self, model_alias, parse=True, output_json=False):
        return self.read_output_model(model_alias=model_alias,
                                      parse=parse,
                                      output_json=output_json)

    def write_output_model(self, component_model):
        self.pipelined_model.write_component_model(component_model)

    def read_output_model(self, model_alias, parse=True, output_json=False):
        return self.pipelined_model.read_component_model(component_name=self.component_name,
                                                         model_alias=model_alias,
                                                         parse=parse,
                                                         output_json=output_json)

    def collect_model(self):
        model_buffers = self.pipelined_model.collect_models()
        return model_buffers

    def save_pipeline_model(self, pipeline_buffer_object):
        self.pipelined_model.save_pipeline_model(pipeline_buffer_object)

    def get_pipeline_model(self):
        return self.pipelined_model.read_pipeline_model()

    def get_component_define(self):
        return self.pipelined_model.get_component_define(component_name=self.component_name)

    def save_output_cache(self, cache_data: typing.Dict[str, CTableABC], cache_meta: dict, cache_name, output_storage_engine, output_storage_address: dict, token=None):
        output_namespace, output_name = default_output_info(task_id=self.task_id, task_version=self.task_version, output_type="cache")
        cache = CacheManager.persistent(cache_name, cache_data, cache_meta, output_namespace, output_name, output_storage_engine, output_storage_address, token=token)
        cache_key = self.tracking_output_cache(cache=cache, cache_name=cache_name)
        return cache_key

    def tracking_output_cache(self, cache: DataCache, cache_name: str) -> str:
        cache_key = CacheManager.record(cache=cache,
                                        job_id=self.job_id,
                                        role=self.role,
                                        party_id=self.party_id,
                                        component_name=self.component_name,
                                        task_id=self.task_id,
                                        task_version=self.task_version,
                                        cache_name=cache_name)
        schedule_logger(self.job_id).info(f"tracking {self.task_id} {self.task_version} output cache, cache key is {cache_key}")
        return cache_key

    def get_output_cache(self, cache_key=None, cache_name=None):
        caches = self.query_output_cache(cache_key=cache_key, cache_name=cache_name)
        if caches:
            return CacheManager.load(cache=caches[0])
        else:
            return None, None

    def query_output_cache(self, cache_key=None, cache_name=None) -> typing.List[DataCache]:
        caches = CacheManager.query(job_id=self.job_id, role=self.role, party_id=self.party_id, component_name=self.component_name, cache_name=cache_name, cache_key=cache_key)
        group = {}
        # only the latest version of the task output is retrieved
        for cache in caches:
            group_key = f"{cache.task_id}-{cache.name}"
            if group_key not in group:
                group[group_key] = cache
            elif cache.task_version > group[group_key].task_version:
                group[group_key] = cache
        return list(group.values())

    def query_output_cache_record(self):
        return CacheManager.query_record(job_id=self.job_id, role=self.role, party_id=self.party_id, component_name=self.component_name,
                                         task_version=self.task_version)

    @DB.connection_context()
    def insert_summary_into_db(self, summary_data: dict, need_serialize=True):
        try:
            summary_model = self.get_dynamic_db_model(ComponentSummary, self.job_id)
            DB.create_tables([summary_model])
            summary_obj = summary_model.get_or_none(
                summary_model.f_job_id == self.job_id,
                summary_model.f_component_name == self.component_name,
                summary_model.f_role == self.role,
                summary_model.f_party_id == self.party_id,
                summary_model.f_task_id == self.task_id,
                summary_model.f_task_version == self.task_version
            )
            if summary_obj:
                summary_obj.f_summary = serialize_b64(summary_data, to_str=True) if need_serialize else summary_data
                summary_obj.f_update_time = current_timestamp()
                summary_obj.save()
            else:
                self.get_dynamic_db_model(ComponentSummary, self.job_id).create(
                    f_job_id=self.job_id,
                    f_component_name=self.component_name,
                    f_role=self.role,
                    f_party_id=self.party_id,
                    f_task_id=self.task_id,
                    f_task_version=self.task_version,
                    f_summary=serialize_b64(summary_data, to_str=True),
                    f_create_time=current_timestamp()
                )
        except Exception as e:
            schedule_logger(self.job_id).exception("An exception where querying summary job id: {} "
                                                   "component name: {} to database:\n{}".format(
                self.job_id, self.component_name, e)
            )

    @DB.connection_context()
    def read_summary_from_db(self, need_deserialize=True):
        try:
            summary_model = self.get_dynamic_db_model(ComponentSummary, self.job_id)
            summary = summary_model.get_or_none(
                summary_model.f_job_id == self.job_id,
                summary_model.f_component_name == self.component_name,
                summary_model.f_role == self.role,
                summary_model.f_party_id == self.party_id
            )
            if summary:
                cpn_summary = deserialize_b64(summary.f_summary) if need_deserialize else summary.f_summary
            else:
                cpn_summary = ""
        except Exception as e:
            schedule_logger(self.job_id).exception(e)
            raise e
        return cpn_summary

    @DB.connection_context()
    def reload_summary(self, source_tracker):
        cpn_summary = source_tracker.read_summary_from_db(need_deserialize=False)
        self.insert_summary_into_db(cpn_summary, need_serialize=False)

    def log_output_data_info(self, data_name: str, table_namespace: str, table_name: str):
        self.insert_output_data_info_into_db(data_name=data_name, table_namespace=table_namespace, table_name=table_name)

    @DB.connection_context()
    def insert_output_data_info_into_db(self, data_name: str, table_namespace: str, table_name: str):
        try:
            tracking_output_data_info = self.get_dynamic_db_model(TrackingOutputDataInfo, self.job_id)()
            tracking_output_data_info.f_job_id = self.job_id
            tracking_output_data_info.f_component_name = self.component_name
            tracking_output_data_info.f_task_id = self.task_id
            tracking_output_data_info.f_task_version = self.task_version
            tracking_output_data_info.f_data_name = data_name
            tracking_output_data_info.f_role = self.role
            tracking_output_data_info.f_party_id = self.party_id
            tracking_output_data_info.f_table_namespace = table_namespace
            tracking_output_data_info.f_table_name = table_name
            tracking_output_data_info.f_create_time = current_timestamp()
            self.bulk_insert_into_db(self.get_dynamic_db_model(TrackingOutputDataInfo, self.job_id),
                                     [tracking_output_data_info.to_dict()])
        except Exception as e:
            schedule_logger(self.job_id).exception("An exception where inserted output data info {} {} {} to database:\n{}".format(
                data_name,
                table_namespace,
                table_name,
                e
            ))

    @DB.connection_context()
    def bulk_insert_into_db(self, model, data_source):
        try:
            try:
                DB.create_tables([model])
            except Exception as e:
                schedule_logger(self.job_id).exception(e)
            batch_size = 50 if RuntimeConfig.USE_LOCAL_DATABASE else 1000
            for i in range(0, len(data_source), batch_size):
                with DB.atomic():
                    model.insert_many(data_source[i:i+batch_size]).execute()
            return len(data_source)
        except Exception as e:
            schedule_logger(self.job_id).exception(e)
            return 0

    def save_as_table(self, computing_table, name, namespace):
        if self.job_parameters.storage_engine == StorageEngine.LINKIS_HIVE:
            return
        self.save_output_data(computing_table=computing_table,
                              output_storage_engine=self.job_parameters.storage_engine,
                              output_storage_address=self.job_parameters.engines_address.get(EngineType.STORAGE, {}),
                              output_table_namespace=namespace, output_table_name=name)

    @DB.connection_context()
    def clean_metrics(self):
        return self.metric_manager.clean_metrics()

    @DB.connection_context()
    def get_metric_list(self, job_level: bool = False):
        return self.metric_manager.get_metric_list(job_level=job_level)

    @DB.connection_context()
    def reload_metric(self, source_tracker):
        return self.metric_manager.reload_metric(source_tracker.metric_manager)

    def get_output_data_info(self, data_name=None):
        return self.read_output_data_info_from_db(data_name=data_name)

    def read_output_data_info_from_db(self, data_name=None):
        filter_dict = {}
        filter_dict["job_id"] = self.job_id
        filter_dict["component_name"] = self.component_name
        filter_dict["role"] = self.role
        filter_dict["party_id"] = self.party_id
        if data_name:
            filter_dict["data_name"] = data_name
        return self.query_output_data_infos(**filter_dict)

    @classmethod
    @DB.connection_context()
    def query_output_data_infos(cls, **kwargs) -> typing.List[TrackingOutputDataInfo]:
        try:
            tracking_output_data_info_model = cls.get_dynamic_db_model(TrackingOutputDataInfo, kwargs.get("job_id"))
            filters = []
            for f_n, f_v in kwargs.items():
                attr_name = 'f_%s' % f_n
                if hasattr(tracking_output_data_info_model, attr_name):
                    filters.append(operator.attrgetter('f_%s' % f_n)(tracking_output_data_info_model) == f_v)
            if filters:
                output_data_infos_tmp = tracking_output_data_info_model.select().where(*filters)
            else:
                output_data_infos_tmp = tracking_output_data_info_model.select()
            output_data_infos_group = {}
            # only the latest version of the task output data is retrieved
            for output_data_info in output_data_infos_tmp:
                group_key = cls.get_output_data_group_key(output_data_info.f_task_id, output_data_info.f_data_name)
                if group_key not in output_data_infos_group:
                    output_data_infos_group[group_key] = output_data_info
                elif output_data_info.f_task_version > output_data_infos_group[group_key].f_task_version:
                    output_data_infos_group[group_key] = output_data_info
            return list(output_data_infos_group.values())
        except Exception as e:
            return []

    @classmethod
    def get_output_data_group_key(cls, task_id, data_name):
        return task_id + data_name

    def clean_task(self, runtime_conf):
        schedule_logger(self.job_id).info('clean task {} {} on {} {}'.format(self.task_id,
                                                                             self.task_version,
                                                                             self.role,
                                                                             self.party_id))
        try:
            with session.Session() as sess:
                # clean up temporary tables
                computing_temp_namespace = job_utils.generate_session_id(task_id=self.task_id,
                                                                         task_version=self.task_version,
                                                                         role=self.role,
                                                                         party_id=self.party_id)
                if self.job_parameters.computing_engine == ComputingEngine.EGGROLL:
                    session_options = {"eggroll.session.processors.per.node": 1}
                else:
                    session_options = {}
                try:
                    if self.job_parameters.computing_engine != ComputingEngine.LINKIS_SPARK:
                        sess.init_computing(computing_session_id=f"{computing_temp_namespace}_clean", options=session_options)
                        sess.computing.cleanup(namespace=computing_temp_namespace, name="*")
                        schedule_logger(self.job_id).info('clean table by namespace {} on {} {} done'.format(computing_temp_namespace,
                                                                                                             self.role,
                                                                                                             self.party_id))
                        # clean up the last tables of the federation
                        federation_temp_namespace = job_utils.generate_task_version_id(self.task_id, self.task_version)
                        sess.computing.cleanup(namespace=federation_temp_namespace, name="*")
                        schedule_logger(self.job_id).info('clean table by namespace {} on {} {} done'.format(federation_temp_namespace,
                                                                                                             self.role,
                                                                                                             self.party_id))
                    if self.job_parameters.federation_engine == FederationEngine.RABBITMQ and self.role != "local":
                        schedule_logger(self.job_id).info('rabbitmq start clean up')
                        parties = [Party(k, p) for k, v in runtime_conf['role'].items() for p in v]
                        federation_session_id = job_utils.generate_task_version_id(self.task_id, self.task_version)
                        component_parameters_on_party = copy.deepcopy(runtime_conf)
                        component_parameters_on_party["local"] = {"role": self.role, "party_id": self.party_id}
                        sess.init_federation(federation_session_id=federation_session_id,
                                             runtime_conf=component_parameters_on_party,
                                             service_conf=self.job_parameters.engines_address.get(EngineType.FEDERATION, {}))
                        sess._federation_session.cleanup(parties)
                        schedule_logger(self.job_id).info('rabbitmq clean up success')

                    #TODO optimize the clean process
                    if self.job_parameters.federation_engine == FederationEngine.PULSAR and self.role != "local":
                        schedule_logger(self.job_id).info('start to clean up pulsar topics')
                        parties = [Party(k, p) for k, v in runtime_conf['role'].items() for p in v]
                        federation_session_id = job_utils.generate_task_version_id(self.task_id, self.task_version)
                        component_parameters_on_party = copy.deepcopy(runtime_conf)
                        component_parameters_on_party["local"] = {"role": self.role, "party_id": self.party_id}
                        sess.init_federation(federation_session_id=federation_session_id,
                                             runtime_conf=component_parameters_on_party,
                                             service_conf=self.job_parameters.engines_address.get(EngineType.FEDERATION, {}))
                        sess._federation_session.cleanup(parties)
                        schedule_logger(self.job_id).info('pulsar topic clean up success')
                except Exception as e:
                    schedule_logger(self.job_id).exception("cleanup error")
                finally:
                    sess.destroy_all_sessions()
                return True
        except Exception as e:
            schedule_logger(self.job_id).exception(e)
            return False

    @DB.connection_context()
    def save_machine_learning_model_info(self):
        try:
            record = MLModel.get_or_none(MLModel.f_model_version == self.job_id,
                                         MLModel.f_role == self.role,
                                         MLModel.f_model_id == self.model_id,
                                         MLModel.f_party_id == self.party_id)
            if not record:
                job = Job.get_or_none(Job.f_job_id == self.job_id)
                pipeline = self.pipelined_model.read_pipeline_model()
                if job:
                    job_data = job.to_dict()
                    model_info = {
                        'job_id': job_data.get("f_job_id"),
                        'role': self.role,
                        'party_id': self.party_id,
                        'roles': job_data.get("f_roles"),
                        'model_id': self.model_id,
                        'model_version': self.model_version,
                        'initiator_role': job_data.get('f_initiator_role'),
                        'initiator_party_id': job_data.get('f_initiator_party_id'),
                        'runtime_conf': job_data.get('f_runtime_conf'),
                        'work_mode': job_data.get('f_work_mode'),
                        'train_dsl': job_data.get('f_dsl'),
                        'train_runtime_conf': job_data.get('f_train_runtime_conf'),
                        'size': self.get_model_size(),
                        'job_status': job_data.get('f_status'),
                        'parent': pipeline.parent,
                        'fate_version': pipeline.fate_version,
                        'runtime_conf_on_party': json_loads(pipeline.runtime_conf_on_party),
                        'parent_info': json_loads(pipeline.parent_info),
                        'inference_dsl': json_loads(pipeline.inference_dsl)
                    }
                    model_utils.save_model_info(model_info)

                    schedule_logger(self.job_id).info(
                        'save {} model info done. model id: {}, model version: {}.'.format(self.job_id,
                                                                                           self.model_id,
                                                                                           self.model_version))
                else:
                    schedule_logger(self.job_id).info(
                        'save {} model info failed, no job found in db. '
                        'model id: {}, model version: {}.'.format(self.job_id,
                                                                  self.model_id,
                                                                  self.model_version))
            else:
                schedule_logger(self.job_id).info('model {} info has already existed in database.'.format(self.job_id))
        except Exception as e:
            schedule_logger(self.job_id).exception(e)

    @classmethod
    def get_dynamic_db_model(cls, base, job_id):
        return type(base.model(table_index=cls.get_dynamic_tracking_table_index(job_id=job_id)))

    @classmethod
    def get_dynamic_tracking_table_index(cls, job_id):
        return job_id[:8]

    def get_model_size(self):
        return self.pipelined_model.calculate_model_file_size()
