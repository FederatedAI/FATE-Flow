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
import os
import importlib
import traceback

from fate_arch import session, storage
from fate_arch.computing import ComputingEngine
from fate_arch.common import file_utils, EngineType, profile
from fate_arch.common.base_utils import current_timestamp, json_dumps
from fate_flow.utils.log_utils import getLogger

from fate_flow.entity import JobConfiguration
from fate_flow.entity.run_status import TaskStatus
from fate_flow.errors import PassError
from fate_flow.entity import RunParameters
from fate_flow.entity import DataCache
from fate_flow.db.runtime_config import RuntimeConfig
from fate_flow.db.component_registry import ComponentRegistry
from fate_flow.manager.data_manager import DataTableTracker
from fate_flow.manager.provider_manager import ProviderManager
from fate_flow.operation.job_tracker import Tracker
from fate_flow.model.checkpoint import CheckpointManager
from fate_flow.scheduling_apps.client.operation_client import OperationClient
from fate_flow.utils import job_utils, schedule_utils
from fate_flow.scheduling_apps.client import TrackerClient
from fate_flow.db.db_models import TrackingOutputDataInfo, fill_db_model_object
from fate_flow.component_env_utils import provider_utils
from fate_flow.worker.task_base_worker import BaseTaskWorker, ComponentInput
from fate_flow.utils.base_utils import get_fate_flow_python_directory


LOGGER = getLogger()


class TaskExecutor(BaseTaskWorker):
    def _run_(self):
        # todo: All function calls where errors should be thrown
        args = self.args
        start_time = current_timestamp()
        try:
            LOGGER.info(f'run {args.component_name} {args.task_id} {args.task_version} on {args.role} {args.party_id} task')
            self.report_info.update({
                "job_id": args.job_id,
                "component_name": args.component_name,
                "task_id": args.task_id,
                "task_version": args.task_version,
                "role": args.role,
                "party_id": args.party_id,
                "run_ip": args.run_ip,
                "run_pid": self.run_pid
            })
            operation_client = OperationClient()
            job_configuration = JobConfiguration(**operation_client.get_job_conf(args.job_id, args.role, args.party_id, args.component_name, args.task_id, args.task_version))
            task_parameters_conf = args.config
            dsl_parser = schedule_utils.get_job_dsl_parser(dsl=job_configuration.dsl,
                                                           runtime_conf=job_configuration.runtime_conf,
                                                           train_runtime_conf=job_configuration.train_runtime_conf,
                                                           pipeline_dsl=None)

            job_parameters = dsl_parser.get_job_parameters(job_configuration.runtime_conf)
            user_name = job_parameters.get(args.role, {}).get(args.party_id, {}).get("user", '')
            LOGGER.info(f"user name:{user_name}")
            src_user = task_parameters_conf.get("src_user")
            task_parameters = RunParameters(**task_parameters_conf)
            job_parameters = task_parameters
            if job_parameters.assistant_role:
                TaskExecutor.monkey_patch()

            job_args_on_party = TaskExecutor.get_job_args_on_party(dsl_parser, job_configuration.runtime_conf_on_party, args.role, args.party_id)
            component = dsl_parser.get_component_info(component_name=args.component_name)
            module_name = component.get_module()
            task_input_dsl = component.get_input()
            task_output_dsl = component.get_output()

            kwargs = {
                'job_id': args.job_id,
                'role': args.role,
                'party_id': args.party_id,
                'component_name': args.component_name,
                'task_id': args.task_id,
                'task_version': args.task_version,
                'model_id': job_parameters.model_id,
                'model_version': job_parameters.model_version,
                'component_module_name': module_name,
                'job_parameters': job_parameters,
            }
            tracker = Tracker(**kwargs)
            tracker_client = TrackerClient(**kwargs)
            checkpoint_manager = CheckpointManager(**kwargs)

            self.report_info["party_status"] = TaskStatus.RUNNING
            self.report_task_info_to_driver()

            previous_components_parameters = tracker_client.get_model_run_parameters()
            LOGGER.info(f"previous_components_parameters:\n{json_dumps(previous_components_parameters, indent=4)}")

            component_provider, component_parameters_on_party, user_specified_parameters = ProviderManager.get_component_run_info(dsl_parser=dsl_parser,
                                                                                                                                  component_name=args.component_name,
                                                                                                                                  role=args.role,
                                                                                                                                  party_id=args.party_id,
                                                                                                                                  previous_components_parameters=previous_components_parameters)
            RuntimeConfig.set_component_provider(component_provider)
            LOGGER.info(f"component parameters on party:\n{json_dumps(component_parameters_on_party, indent=4)}")
            flow_feeded_parameters = {"output_data_name": task_output_dsl.get("data")}

            # init environment, process is shared globally
            RuntimeConfig.init_config(COMPUTING_ENGINE=job_parameters.computing_engine,
                                      FEDERATION_ENGINE=job_parameters.federation_engine,
                                      FEDERATED_MODE=job_parameters.federated_mode)

            if RuntimeConfig.COMPUTING_ENGINE == ComputingEngine.EGGROLL:
                session_options = task_parameters.eggroll_run.copy()
                session_options["python.path"] = os.getenv("PYTHONPATH")
                session_options["python.venv"] = os.getenv("VIRTUAL_ENV")
            else:
                session_options = {}

            sess = session.Session(session_id=args.session_id)
            sess.as_global()
            sess.init_computing(computing_session_id=args.session_id, options=session_options)
            component_parameters_on_party["job_parameters"] = job_parameters.to_dict()
            roles = job_configuration.runtime_conf["role"]
            if set(roles) == {"local"}:
                LOGGER.info(f"only local roles, pass init federation")
            else:
                sess.init_federation(federation_session_id=args.federation_session_id,
                                     runtime_conf=component_parameters_on_party,
                                     service_conf=job_parameters.engines_address.get(EngineType.FEDERATION, {}))
            LOGGER.info(f'run {args.component_name} {args.task_id} {args.task_version} on {args.role} {args.party_id} task')
            LOGGER.info(f"component parameters on party:\n{json_dumps(component_parameters_on_party, indent=4)}")
            LOGGER.info(f"task input dsl {task_input_dsl}")
            task_run_args, input_table_list = self.get_task_run_args(job_id=args.job_id, role=args.role, party_id=args.party_id,
                                                                     task_id=args.task_id,
                                                                     task_version=args.task_version,
                                                                     job_args=job_args_on_party,
                                                                     job_parameters=job_parameters,
                                                                     task_parameters=task_parameters,
                                                                     input_dsl=task_input_dsl,
                                                                     )
            if module_name in {"Upload", "Download", "Reader", "Writer", "Checkpoint"}:
                task_run_args["job_parameters"] = job_parameters
            LOGGER.info(f"task input args {task_run_args}")

            need_run = component_parameters_on_party.get("ComponentParam", {}).get("need_run", True)
            provider_interface = provider_utils.get_provider_interface(provider=component_provider)
            run_object = provider_interface.get(module_name, ComponentRegistry.get_provider_components(provider_name=component_provider.name, provider_version=component_provider.version)).get_run_obj(self.args.role)
            flow_feeded_parameters.update({"table_info": input_table_list})
            cpn_input = ComponentInput(
                tracker=tracker_client,
                checkpoint_manager=checkpoint_manager,
                task_version_id=job_utils.generate_task_version_id(args.task_id, args.task_version),
                parameters=component_parameters_on_party["ComponentParam"],
                datasets=task_run_args.get("data", None),
                caches=task_run_args.get("cache", None),
                models=dict(
                    model=task_run_args.get("model"),
                    isometric_model=task_run_args.get("isometric_model"),
                ),
                job_parameters=job_parameters,
                roles=dict(
                    role=component_parameters_on_party["role"],
                    local=component_parameters_on_party["local"],
                ),
                flow_feeded_parameters=flow_feeded_parameters,
            )
            profile_log_enabled = False
            try:
                if int(os.getenv("FATE_PROFILE_LOG_ENABLED", "0")) > 0:
                    profile_log_enabled = True
            except Exception as e:
                LOGGER.warning(e)
            if profile_log_enabled:
                # add profile logs
                LOGGER.info("profile logging is enabled")
                profile.profile_start()
                cpn_output = run_object.run(cpn_input)
                sess.wait_remote_all_done()
                profile.profile_ends()
            else:
                LOGGER.info("profile logging is disabled")
                cpn_output = run_object.run(cpn_input)
                sess.wait_remote_all_done()

            output_table_list = []
            LOGGER.info(f"task output data {cpn_output.data}")
            for index, data in enumerate(cpn_output.data):
                data_name = task_output_dsl.get('data')[index] if task_output_dsl.get('data') else '{}'.format(index)
                #todo: the token depends on the engine type, maybe in job parameters
                persistent_table_namespace, persistent_table_name = tracker.save_output_data(
                    computing_table=data,
                    output_storage_engine=job_parameters.storage_engine,
                    token={"username": user_name})
                if persistent_table_namespace and persistent_table_name:
                    tracker.log_output_data_info(data_name=data_name,
                                                 table_namespace=persistent_table_namespace,
                                                 table_name=persistent_table_name)
                    output_table_list.append({"namespace": persistent_table_namespace, "name": persistent_table_name})
            self.log_output_data_table_tracker(args.job_id, input_table_list, output_table_list)

            # There is only one model output at the current dsl version.
            tracker_client.save_component_output_model(model_buffers=cpn_output.model,
                                                       model_alias=task_output_dsl['model'][0] if task_output_dsl.get('model') else 'default',
                                                       user_specified_run_parameters=user_specified_parameters)
            if cpn_output.cache is not None:
                for i, cache in enumerate(cpn_output.cache):
                    if cache is None:
                        continue
                    name = task_output_dsl.get("cache")[i] if "cache" in task_output_dsl else str(i)
                    if isinstance(cache, DataCache):
                        tracker.tracking_output_cache(cache, cache_name=name)
                    elif isinstance(cache, tuple):
                        tracker.save_output_cache(cache_data=cache[0],
                                                  cache_meta=cache[1],
                                                  cache_name=name,
                                                  output_storage_engine=job_parameters.storage_engine,
                                                  output_storage_address=job_parameters.engines_address.get(EngineType.STORAGE, {}),
                                                  token={"username": user_name})
                    else:
                        raise RuntimeError(f"can not support type {type(cache)} module run object output cache")
            if need_run:
                self.report_info["party_status"] = TaskStatus.SUCCESS
            else:
                self.report_info["party_status"] = TaskStatus.PASS
        except PassError as e:
            self.report_info["party_status"] = TaskStatus.PASS
        except Exception as e:
            traceback.print_exc()
            self.report_info["party_status"] = TaskStatus.FAILED
            LOGGER.exception(e)
        finally:
            try:
                self.report_info["end_time"] = current_timestamp()
                self.report_info["elapsed"] = self.report_info["end_time"] - start_time
                self.report_task_info_to_driver()
            except Exception as e:
                self.report_info["party_status"] = TaskStatus.FAILED
                traceback.print_exc()
                LOGGER.exception(e)
        msg = f"finish {args.component_name} {args.task_id} {args.task_version} on {args.role} {args.party_id} with {self.report_info['party_status']}"
        LOGGER.info(msg)
        print(msg)
        return self.report_info

    @classmethod
    def log_output_data_table_tracker(cls, job_id, input_table_list, output_table_list):
        try:
            parent_number = 0
            if len(input_table_list) > 1 and len(output_table_list)>1:
                # TODO
                return
            for input_table in input_table_list:
                for output_table in output_table_list:
                    DataTableTracker.create_table_tracker(output_table.get("name"), output_table.get("namespace"),
                                                          entity_info={
                                                              "have_parent": True,
                                                              "parent_table_namespace": input_table.get("namespace"),
                                                              "parent_table_name": input_table.get("name"),
                                                              "parent_number": parent_number,
                                                              "job_id": job_id
                                                          })
                parent_number +=1
        except Exception as e:
            LOGGER.exception(e)

    @classmethod
    def get_job_args_on_party(cls, dsl_parser, job_runtime_conf, role, party_id):
        party_index = job_runtime_conf["role"][role].index(int(party_id))
        job_args = dsl_parser.get_args_input()
        job_args_on_party = job_args[role][party_index].get('args') if role in job_args else {}
        return job_args_on_party

    @classmethod
    def get_task_run_args(cls, job_id, role, party_id, task_id, task_version,
                          job_args, job_parameters: RunParameters, task_parameters: RunParameters,
                          input_dsl, filter_type=None, filter_attr=None, get_input_table=False):
        task_run_args = {}
        input_table = {}
        input_table_info_list = []
        if 'idmapping' in role:
            return {}
        for input_type, input_detail in input_dsl.items():
            if filter_type and input_type not in filter_type:
                continue
            if input_type == 'data':
                this_type_args = task_run_args[input_type] = task_run_args.get(input_type, {})
                for data_type, data_list in input_detail.items():
                    data_dict = {}
                    for data_key in data_list:
                        data_key_item = data_key.split('.')
                        data_dict[data_key_item[0]] = {data_type: []}
                    for data_key in data_list:
                        data_key_item = data_key.split('.')
                        search_component_name, search_data_name = data_key_item[0], data_key_item[1]
                        storage_table_meta = None
                        tracker_client = TrackerClient(job_id=job_id, role=role, party_id=party_id,
                                                       component_name=search_component_name,
                                                       task_id=task_id, task_version=task_version)
                        if search_component_name == 'args':
                            if job_args.get('data', {}).get(search_data_name).get('namespace', '') and job_args.get(
                                    'data', {}).get(search_data_name).get('name', ''):
                                storage_table_meta = storage.StorageTableMeta(
                                    name=job_args['data'][search_data_name]['name'],
                                    namespace=job_args['data'][search_data_name]['namespace'])
                        else:
                            upstream_output_table_infos_json = tracker_client.get_output_data_info(
                                data_name=search_data_name)
                            if upstream_output_table_infos_json:
                                tracker = Tracker(job_id=job_id, role=role, party_id=party_id,
                                                  component_name=search_component_name,
                                                  task_id=task_id, task_version=task_version)
                                upstream_output_table_infos = []
                                for _ in upstream_output_table_infos_json:
                                    upstream_output_table_infos.append(fill_db_model_object(
                                        Tracker.get_dynamic_db_model(TrackingOutputDataInfo, job_id)(), _))
                                output_tables_meta = tracker.get_output_data_table(upstream_output_table_infos)
                                if output_tables_meta:
                                    storage_table_meta = output_tables_meta.get(search_data_name, None)
                        args_from_component = this_type_args[search_component_name] = this_type_args.get(
                            search_component_name, {})
                        if get_input_table and storage_table_meta:
                            input_table[data_key] = {'namespace': storage_table_meta.get_namespace(),
                                                     'name': storage_table_meta.get_name()}
                            computing_table = None
                        elif storage_table_meta:
                            LOGGER.info(f"load computing table use {task_parameters.computing_partitions}")
                            computing_table = session.get_computing_session().load(
                                storage_table_meta.get_address(),
                                schema=storage_table_meta.get_schema(),
                                partitions=task_parameters.computing_partitions)
                            input_table_info_list.append({'namespace': storage_table_meta.get_namespace(),
                                                          'name': storage_table_meta.get_name()})
                        else:
                            computing_table = None

                        if not computing_table or not filter_attr or not filter_attr.get("data", None):
                            data_dict[search_component_name][data_type].append(computing_table)
                            args_from_component[data_type] = data_dict[search_component_name][data_type]
                        else:
                            args_from_component[data_type] = dict(
                                [(a, getattr(computing_table, "get_{}".format(a))()) for a in filter_attr["data"]])
            elif input_type == "cache":
                this_type_args = task_run_args[input_type] = task_run_args.get(input_type, {})
                for search_key in input_detail:
                    search_component_name, cache_name = search_key.split(".")
                    tracker = Tracker(job_id=job_id, role=role, party_id=party_id, component_name=search_component_name)
                    this_type_args[search_component_name] = tracker.get_output_cache(cache_name=cache_name)
            elif input_type in {'model', 'isometric_model'}:
                this_type_args = task_run_args[input_type] = task_run_args.get(input_type, {})
                for dsl_model_key in input_detail:
                    dsl_model_key_items = dsl_model_key.split('.')
                    if len(dsl_model_key_items) == 2:
                        search_component_name, search_model_alias = dsl_model_key_items[0], dsl_model_key_items[1]
                    elif len(dsl_model_key_items) == 3 and dsl_model_key_items[0] == 'pipeline':
                        search_component_name, search_model_alias = dsl_model_key_items[1], dsl_model_key_items[2]
                    else:
                        raise Exception('get input {} failed'.format(input_type))
                    tracker_client = TrackerClient(job_id=job_id, role=role, party_id=party_id, component_name=search_component_name, model_id=job_parameters.model_id, model_version=job_parameters.model_version)
                    models = tracker_client.read_component_output_model(search_model_alias)
                    this_type_args[search_component_name] = models
            else:
                raise Exception(f"not support {input_type} input type")
        if get_input_table:
            return input_table
        return task_run_args, input_table_info_list

    @classmethod
    def monkey_patch(cls):
        package_name = "monkey_patch"
        package_path = os.path.join(get_fate_flow_python_directory(), "fate_flow", package_name)
        if not os.path.exists(package_path):
            return
        for f in os.listdir(package_path):
            f_path = os.path.join(get_fate_flow_python_directory(), "fate_flow", package_name, f)
            if not os.path.isdir(f_path) or "__pycache__" in f_path:
                continue
            patch_module = importlib.import_module("fate_flow." + package_name + '.' + f + '.monkey_patch')
            patch_module.patch_all()


if __name__ == '__main__':
    worker = TaskExecutor()
    worker.run()
    worker.report_task_info_to_driver()

