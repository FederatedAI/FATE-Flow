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
import shutil

from fate_arch.common import EngineType
from fate_arch.common import engine_utils
from fate_arch.common.base_utils import json_dumps, current_timestamp
from fate_arch.computing import ComputingEngine
from fate_flow.controller.task_controller import TaskController
from fate_flow.db.job_default_config import JobDefaultConfig
from fate_flow.db.runtime_config import RuntimeConfig
from fate_flow.entity import RunParameters
from fate_flow.entity.run_status import JobStatus, EndStatus, TaskStatus
from fate_flow.entity.run_status import JobStatus, EndStatus, JobInheritanceStatus
from fate_flow.entity.types import InputSearchType, WorkerName
from fate_flow.manager.provider_manager import ProviderManager
from fate_flow.manager.resource_manager import ResourceManager
from fate_flow.manager.worker_manager import WorkerManager
from fate_flow.model.checkpoint import CheckpointManager
from fate_flow.operation.job_saver import JobSaver
from fate_flow.operation.job_tracker import Tracker
from fate_flow.pipelined_model.pipelined_model import PipelinedModel
from fate_flow.protobuf.python import pipeline_pb2
from fate_flow.settings import USE_AUTHENTICATION, USE_DATA_AUTHENTICATION, ENGINES
from fate_flow.utils import job_utils, schedule_utils, data_utils, log_utils, model_utils
from fate_flow.utils.authentication_utils import authentication_check
from fate_flow.utils.authentication_utils import data_authentication_check
from fate_flow.utils.log_utils import schedule_logger
from fate_flow.entity.types import TaskCleanResourceType


class JobController(object):
    @classmethod
    def create_job(cls, job_id, role, party_id, job_info):
        # parse job configuration
        dsl = job_info['dsl']
        runtime_conf = job_info['runtime_conf']
        train_runtime_conf = job_info['train_runtime_conf']
        if USE_AUTHENTICATION:
            authentication_check(src_role=job_info.get('src_role', None), src_party_id=job_info.get('src_party_id', None),
                                 dsl=dsl, runtime_conf=runtime_conf, role=role, party_id=party_id)

        dsl_parser = schedule_utils.get_job_dsl_parser(dsl=dsl,
                                                       runtime_conf=runtime_conf,
                                                       train_runtime_conf=train_runtime_conf)
        job_parameters = dsl_parser.get_job_parameters(runtime_conf)
        schedule_logger(job_id).info('job parameters:{}'.format(job_parameters))
        dest_user = job_parameters.get(role, {}).get(party_id, {}).get('user', '')
        user = {}
        src_party_id = int(job_info['src_party_id']) if job_info.get('src_party_id') else 0
        src_role = job_info.get('src_role', '')
        src_user = job_parameters.get(src_role, {}).get(src_party_id, {}).get('user', '') if src_role else ''
        for _role, party_id_item in job_parameters.items():
            user[_role] = {}
            for _party_id, _parameters in party_id_item.items():
                user[_role][_party_id] = _parameters.get("user", "")
        schedule_logger(job_id).info('job user:{}'.format(user))
        if USE_DATA_AUTHENTICATION:
            job_args = dsl_parser.get_args_input()
            schedule_logger(job_id).info('job args:{}'.format(job_args))
            dataset_dict = cls.get_dataset(False, role, party_id, runtime_conf.get("role"), job_args)
            dataset_list = []
            if dataset_dict.get(role, {}).get(party_id):
                for k, v in dataset_dict[role][party_id].items():
                    dataset_list.append({"namespace": v.split('.')[0], "table_name": v.split('.')[1]})
            data_authentication_check(src_role=job_info.get('src_role'), src_party_id=job_info.get('src_party_id'),
                                      src_user=src_user, dest_user=dest_user, dataset_list=dataset_list)
        job_parameters = RunParameters(**job_parameters.get(role, {}).get(party_id, {}))

        # save new job into db
        if role == job_info["initiator_role"] and party_id == job_info["initiator_party_id"]:
            is_initiator = True
        else:
            is_initiator = False
        job_info["status"] = JobStatus.READY
        job_info["user_id"] = dest_user
        job_info["src_user"] = src_user
        job_info["user"] = user
        # this party configuration
        job_info["role"] = role
        job_info["party_id"] = party_id
        job_info["is_initiator"] = is_initiator
        job_info["progress"] = 0
        cls.create_job_parameters_on_party(role=role, party_id=party_id, job_parameters=job_parameters)
        # update job parameters on party
        job_info["runtime_conf_on_party"]["job_parameters"] = job_parameters.to_dict()
        JobSaver.create_job(job_info=job_info)
        schedule_logger(job_id).info("start initialize tasks")
        initialized_result, provider_group = cls.initialize_tasks(job_id=job_id, role=role, party_id=party_id, run_on_this_party=True,
                                                                  initiator_role=job_info["initiator_role"], initiator_party_id=job_info["initiator_party_id"], job_parameters=job_parameters, dsl_parser=dsl_parser)
        schedule_logger(job_id).info("initialize tasks success")
        for provider_key, group_info in provider_group.items():
            for cpn in group_info["components"]:
                dsl["components"][cpn]["provider"] = provider_key

        roles = job_info['roles']
        cls.initialize_job_tracker(job_id=job_id, role=role, party_id=party_id,
                                   job_parameters=job_parameters, roles=roles, is_initiator=is_initiator, dsl_parser=dsl_parser)

        job_utils.save_job_conf(job_id=job_id,
                                role=role,
                                party_id=party_id,
                                dsl=dsl,
                                runtime_conf=runtime_conf,
                                runtime_conf_on_party=job_info["runtime_conf_on_party"],
                                train_runtime_conf=train_runtime_conf,
                                pipeline_dsl=None)
        return {"components": initialized_result}

    @classmethod
    def set_federated_mode(cls, job_parameters: RunParameters):
        if not job_parameters.federated_mode:
            job_parameters.federated_mode = ENGINES["federated_mode"]

    @classmethod
    def set_engines(cls, job_parameters: RunParameters, engine_type=None):
        engines = engine_utils.get_engines()
        if not engine_type:
            engine_type = {EngineType.COMPUTING, EngineType.FEDERATION, EngineType.STORAGE}
        for k in engine_type:
            setattr(job_parameters, f"{k}_engine", engines[k])

    @classmethod
    def create_common_job_parameters(cls, job_id, initiator_role, common_job_parameters: RunParameters):
        JobController.set_federated_mode(job_parameters=common_job_parameters)
        JobController.set_engines(job_parameters=common_job_parameters, engine_type={EngineType.COMPUTING})
        JobController.fill_default_job_parameters(job_id=job_id, job_parameters=common_job_parameters)
        JobController.adapt_job_parameters(role=initiator_role, job_parameters=common_job_parameters, create_initiator_baseline=True)

    @classmethod
    def create_job_parameters_on_party(cls, role, party_id, job_parameters: RunParameters):
        JobController.set_engines(job_parameters=job_parameters)
        cls.fill_party_specific_parameters(role=role,
                                           party_id=party_id,
                                           job_parameters=job_parameters)

    @classmethod
    def fill_party_specific_parameters(cls, role, party_id, job_parameters: RunParameters):
        cls.adapt_job_parameters(role=role, job_parameters=job_parameters)
        engines_info = cls.get_job_engines_address(job_parameters=job_parameters)
        cls.check_parameters(job_parameters=job_parameters,
                             role=role, party_id=party_id, engines_info=engines_info)

    @classmethod
    def fill_default_job_parameters(cls, job_id, job_parameters: RunParameters):
        keys = {"task_parallelism", "auto_retries", "auto_retry_delay", "federated_status_collect_type"}
        for key in keys:
            if hasattr(job_parameters, key) and getattr(job_parameters, key) is None:
                if hasattr(JobDefaultConfig, key):
                    setattr(job_parameters, key, getattr(JobDefaultConfig, key))
                else:
                    schedule_logger(job_id).warning(f"can not found {key} job parameter default value from job_default_settings")

    @classmethod
    def adapt_job_parameters(cls, role, job_parameters: RunParameters, create_initiator_baseline=False):
        ResourceManager.adapt_engine_parameters(
            role=role, job_parameters=job_parameters, create_initiator_baseline=create_initiator_baseline)
        if create_initiator_baseline:
            if job_parameters.task_parallelism is None:
                job_parameters.task_parallelism = JobDefaultConfig.task_parallelism
            if job_parameters.federated_status_collect_type is None:
                job_parameters.federated_status_collect_type = JobDefaultConfig.federated_status_collect_type
        if create_initiator_baseline and not job_parameters.computing_partitions:
            job_parameters.computing_partitions = job_parameters.adaptation_parameters[
                "task_cores_per_node"] * job_parameters.adaptation_parameters["task_nodes"]

    @classmethod
    def get_job_engines_address(cls, job_parameters: RunParameters):
        engines_info = {}
        engine_list = [
            (EngineType.COMPUTING, job_parameters.computing_engine),
            (EngineType.FEDERATION, job_parameters.federation_engine),
            (EngineType.STORAGE, job_parameters.storage_engine)
        ]
        for engine_type, engine_name in engine_list:
            engine_info = ResourceManager.get_engine_registration_info(
                engine_type=engine_type, engine_name=engine_name)
            job_parameters.engines_address[engine_type] = engine_info.f_engine_config if engine_info else {}
            engines_info[engine_type] = engine_info
        return engines_info

    @classmethod
    def check_parameters(cls, job_parameters: RunParameters, role, party_id, engines_info):
        status, cores_submit, max_cores_per_job = ResourceManager.check_resource_apply(
            job_parameters=job_parameters, role=role, party_id=party_id, engines_info=engines_info)
        if not status:
            msg = ""
            msg2 = "default value is fate_flow/settings.py#DEFAULT_TASK_CORES_PER_NODE, refer fate_flow/examples/simple/simple_job_conf.json"
            if job_parameters.computing_engine in {ComputingEngine.EGGROLL, ComputingEngine.STANDALONE}:
                msg = "please use task_cores job parameters to set request task cores or you can customize it with eggroll_run job parameters"
            elif job_parameters.computing_engine in {ComputingEngine.SPARK}:
                msg = "please use task_cores job parameters to set request task cores or you can customize it with spark_run job parameters"
            raise RuntimeError(
                f"max cores per job is {max_cores_per_job} base on (fate_flow/settings#MAX_CORES_PERCENT_PER_JOB * conf/service_conf.yaml#nodes * conf/service_conf.yaml#cores_per_node), expect {cores_submit} cores, {msg}, {msg2}")

    @classmethod
    def gen_updated_parameters(cls, job_id, initiator_role, initiator_party_id, input_job_parameters, input_component_parameters):
        # todo: check can not update job parameters
        job_configuration = job_utils.get_job_configuration(job_id=job_id,
                                                            role=initiator_role,
                                                            party_id=initiator_party_id)
        updated_job_parameters = job_configuration.runtime_conf["job_parameters"]
        updated_component_parameters = job_configuration.runtime_conf["component_parameters"]
        if input_job_parameters:
            if input_job_parameters.get("common"):
                common_job_parameters = RunParameters(**input_job_parameters["common"])
                cls.create_common_job_parameters(job_id=job_id, initiator_role=initiator_role, common_job_parameters=common_job_parameters)
                for attr in {"model_id", "model_version"}:
                    setattr(common_job_parameters, attr, updated_job_parameters["common"].get(attr))
                updated_job_parameters["common"] = common_job_parameters.to_dict()
            # not support role
        updated_components = set()
        if input_component_parameters:
            cls.merge_update(input_component_parameters, updated_component_parameters)
        return updated_job_parameters, updated_component_parameters, list(updated_components)

    @classmethod
    def merge_update(cls, inputs: dict, results: dict):
        if not isinstance(inputs, dict) or not isinstance(results, dict):
            raise ValueError(f"must both dict, but {type(inputs)} inputs and {type(results)} results")
        for k, v in inputs.items():
            if k not in results:
                results[k] = v
            elif isinstance(v, dict):
                cls.merge_update(v, results[k])
            else:
                results[k] = v

    @classmethod
    def update_parameter(cls, job_id, role, party_id, updated_parameters: dict):
        job_configuration = job_utils.get_job_configuration(job_id=job_id,
                                                            role=role,
                                                            party_id=party_id)
        job_parameters = updated_parameters.get("job_parameters")
        component_parameters = updated_parameters.get("component_parameters")
        if job_parameters:
            job_configuration.runtime_conf["job_parameters"] = job_parameters
            job_parameters = RunParameters(**job_parameters["common"])
            cls.create_job_parameters_on_party(role=role,
                                               party_id=party_id,
                                               job_parameters=job_parameters)
            job_configuration.runtime_conf_on_party["job_parameters"] = job_parameters.to_dict()
        if component_parameters:
            job_configuration.runtime_conf["component_parameters"] = component_parameters
            job_configuration.runtime_conf_on_party["component_parameters"] = component_parameters

        job_info = {}
        job_info["job_id"] = job_id
        job_info["role"] = role
        job_info["party_id"] = party_id
        job_info["runtime_conf"] = job_configuration.runtime_conf
        job_info["runtime_conf_on_party"] = job_configuration.runtime_conf_on_party
        JobSaver.update_job(job_info)

    @classmethod
    def initialize_task(cls, role, party_id, task_info: dict):
        task_info["role"] = role
        task_info["party_id"] = party_id
        initialized_result, provider_group = cls.initialize_tasks(components=[task_info["component_name"]], **task_info)
        return initialized_result

    @classmethod
    def initialize_tasks(cls, job_id, role, party_id, run_on_this_party, initiator_role, initiator_party_id, job_parameters: RunParameters = None, dsl_parser=None, components: list = None, **kwargs):
        common_task_info = {}
        common_task_info["job_id"] = job_id
        common_task_info["initiator_role"] = initiator_role
        common_task_info["initiator_party_id"] = initiator_party_id
        common_task_info["role"] = role
        common_task_info["party_id"] = party_id
        common_task_info["run_on_this_party"] = run_on_this_party
        common_task_info["federated_mode"] = kwargs.get("federated_mode", job_parameters.federated_mode if job_parameters else None)
        common_task_info["federated_status_collect_type"] = kwargs.get("federated_status_collect_type", job_parameters.federated_status_collect_type if job_parameters else None)
        common_task_info["auto_retries"] = kwargs.get("auto_retries", job_parameters.auto_retries if job_parameters else None)
        common_task_info["auto_retry_delay"] = kwargs.get("auto_retry_delay", job_parameters.auto_retry_delay if job_parameters else None)
        common_task_info["task_version"] = kwargs.get("task_version")
        if dsl_parser is None:
            dsl_parser = schedule_utils.get_job_dsl_parser_by_job_id(job_id)
        provider_group = ProviderManager.get_job_provider_group(dsl_parser=dsl_parser,
                                                                components=components)
        initialized_result = {}
        for group_key, group_info in provider_group.items():
            initialized_config = {}
            initialized_config.update(group_info)
            initialized_config["common_task_info"] = common_task_info
            if run_on_this_party:
                code, _result = WorkerManager.start_general_worker(worker_name=WorkerName.TASK_INITIALIZER,
                                                                   job_id=job_id,
                                                                   role=role,
                                                                   party_id=party_id,
                                                                   initialized_config=initialized_config,
                                                                   run_in_subprocess=False if initialized_config["if_default_provider"] else True)
                initialized_result.update(_result)
            else:
                cls.initialize_task_holder_for_scheduling(role=role,
                                                          party_id=party_id,
                                                          components=initialized_config["components"],
                                                          common_task_info=common_task_info,
                                                          provider_info=initialized_config["provider"])
        return initialized_result, provider_group

    @classmethod
    def initialize_task_holder_for_scheduling(cls, role, party_id, components, common_task_info, provider_info):
        for component_name in components:
            task_info = {}
            task_info.update(common_task_info)
            task_info["component_name"] = component_name
            task_info["component_module"] = ""
            task_info["provider_info"] = provider_info
            task_info["component_parameters"] = {}
            TaskController.create_task(role=role, party_id=party_id,
                                       run_on_this_party=common_task_info["run_on_this_party"],
                                       task_info=task_info)

    @classmethod
    def initialize_job_tracker(cls, job_id, role, party_id, job_parameters: RunParameters, roles, is_initiator, dsl_parser):
        tracker = Tracker(job_id=job_id, role=role, party_id=party_id,
                          model_id=job_parameters.model_id,
                          model_version=job_parameters.model_version,
                          job_parameters=job_parameters)
        if job_parameters.job_type != "predict":
            tracker.init_pipeline_model()
        partner = {}
        show_role = {}
        for _role, _role_party in roles.items():
            if is_initiator or _role == role:
                show_role[_role] = show_role.get(_role, [])
                for _party_id in _role_party:
                    if is_initiator or _party_id == party_id:
                        show_role[_role].append(_party_id)

            if _role != role:
                partner[_role] = partner.get(_role, [])
                partner[_role].extend(_role_party)
            else:
                for _party_id in _role_party:
                    if _party_id != party_id:
                        partner[_role] = partner.get(_role, [])
                        partner[_role].append(_party_id)

        job_args = dsl_parser.get_args_input()
        dataset = cls.get_dataset(
            is_initiator, role, party_id, roles, job_args)
        tracker.log_job_view(
            {'partner': partner, 'dataset': dataset, 'roles': show_role})

    @classmethod
    def get_dataset(cls, is_initiator, role, party_id, roles, job_args):
        dataset = {}
        dsl_version = 1
        if job_args.get('dsl_version'):
            if job_args.get('dsl_version') == 2:
                dsl_version = 2
        for _role, _role_party_args in job_args.items():
            if _role == "dsl_version":
                continue
            if is_initiator or _role == role:
                for _party_index in range(len(_role_party_args)):
                    _party_id = roles[_role][_party_index]
                    if is_initiator or _party_id == party_id:
                        dataset[_role] = dataset.get(_role, {})
                        dataset[_role][_party_id] = dataset[_role].get(
                            _party_id, {})
                        if dsl_version == 1:
                            for _data_type, _data_location in _role_party_args[_party_index]['args']['data'].items():
                                dataset[_role][_party_id][_data_type] = '{}.{}'.format(
                                    _data_location['namespace'], _data_location['name'])
                        else:
                            for key in _role_party_args[_party_index].keys():
                                for _data_type, _data_location in _role_party_args[_party_index][key].items():
                                    search_type = data_utils.get_input_search_type(parameters=_data_location)
                                    if search_type is InputSearchType.TABLE_INFO:
                                        dataset[_role][_party_id][key] = '{}.{}'.format(_data_location['namespace'], _data_location['name'])
                                    elif search_type is InputSearchType.JOB_COMPONENT_OUTPUT:
                                        dataset[_role][_party_id][key] = '{}.{}.{}'.format(_data_location['job_id'], _data_location['component_name'], _data_location['data_name'])
                                    else:
                                        dataset[_role][_party_id][key] = "unknown"
        return dataset

    @classmethod
    def query_job_input_args(cls, input_data, role, party_id):
        min_partition = data_utils.get_input_data_min_partitions(
            input_data, role, party_id)
        return {'min_input_data_partition': min_partition}

    @classmethod
    def align_job_args(cls, job_id, role, party_id, job_info):
        job_info["job_id"] = job_id
        job_info["role"] = role
        job_info["party_id"] = party_id
        JobSaver.update_job(job_info)

    @classmethod
    def start_job(cls, job_id, role, party_id, extra_info=None):
        schedule_logger(job_id).info(
            f"try to start job on {role} {party_id}")
        job_info = {
            "job_id": job_id,
            "role": role,
            "party_id": party_id,
            "status": JobStatus.RUNNING,
            "start_time": current_timestamp()
        }
        if extra_info:
            schedule_logger(job_id).info(f"extra info: {extra_info}")
            job_info.update(extra_info)
        cls.update_job_status(job_info=job_info)
        cls.update_job(job_info=job_info)
        schedule_logger(job_id).info(
            f"start job on {role} {party_id} successfully")

    @classmethod
    def update_job(cls, job_info):
        """
        Save to local database
        :param job_info:
        :return:
        """
        return JobSaver.update_job(job_info=job_info)

    @classmethod
    def update_job_status(cls, job_info):
        update_status = JobSaver.update_job_status(job_info=job_info)
        if update_status and EndStatus.contains(job_info.get("status")):
            ResourceManager.return_job_resource(
                job_id=job_info["job_id"], role=job_info["role"], party_id=job_info["party_id"])
        return update_status

    @classmethod
    def stop_jobs(cls, job_id, stop_status, role=None, party_id=None):
        if role and party_id:
            jobs = JobSaver.query_job(
                job_id=job_id, role=role, party_id=party_id)
        else:
            jobs = JobSaver.query_job(job_id=job_id)
        kill_status = True
        kill_details = {}
        for job in jobs:
            kill_job_status, kill_job_details = cls.stop_job(
                job=job, stop_status=stop_status)
            kill_status = kill_status & kill_job_status
            kill_details[job_id] = kill_job_details
        return kill_status, kill_details

    @classmethod
    def stop_job(cls, job, stop_status):
        tasks = JobSaver.query_task(
            job_id=job.f_job_id, role=job.f_role, party_id=job.f_party_id, only_latest=True, reverse=True)
        kill_status = True
        kill_details = {}
        for task in tasks:
            if task.f_status in [TaskStatus.SUCCESS, TaskStatus.WAITING, TaskStatus.PASS]:
                continue
            kill_task_status = TaskController.stop_task(
                task=task, stop_status=stop_status)
            kill_status = kill_status & kill_task_status
            kill_details[task.f_task_id] = 'success' if kill_task_status else 'failed'
        if kill_status:
            job_info = job.to_human_model_dict(only_primary_with=["status"])
            job_info["status"] = stop_status
            JobController.update_job_status(job_info)
        return kill_status, kill_details
        # Job status depends on the final operation result and initiator calculate

    @classmethod
    def save_pipelined_model(cls, job_id, role, party_id):
        schedule_logger(job_id).info(f"start to save pipeline model on {role} {party_id}")
        job_configuration = job_utils.get_job_configuration(job_id=job_id, role=role,
                                                            party_id=party_id)
        runtime_conf_on_party = job_configuration.runtime_conf_on_party
        job_parameters = runtime_conf_on_party.get('job_parameters', {})
        if role in job_parameters.get("assistant_role", []):
            return
        model_id = job_parameters['model_id']
        model_version = job_parameters['model_version']
        job_type = job_parameters.get('job_type', '')
        roles = runtime_conf_on_party['role']
        initiator_role = runtime_conf_on_party['initiator']['role']
        initiator_party_id = runtime_conf_on_party['initiator']['party_id']
        if job_type == 'predict':
            return
        dsl_parser = schedule_utils.get_job_dsl_parser(dsl=job_configuration.dsl,
                                                       runtime_conf=job_configuration.runtime_conf,
                                                       train_runtime_conf=job_configuration.train_runtime_conf)

        components_parameters = {}
        tasks = JobSaver.query_task(job_id=job_id, role=role, party_id=party_id, only_latest=True)
        for task in tasks:
            components_parameters[task.f_component_name] = task.f_component_parameters
        predict_dsl = schedule_utils.fill_inference_dsl(dsl_parser, origin_inference_dsl=job_configuration.dsl, components_parameters=components_parameters)

        pipeline = pipeline_pb2.Pipeline()
        pipeline.inference_dsl = json_dumps(predict_dsl, byte=True)
        pipeline.train_dsl = json_dumps(job_configuration.dsl, byte=True)
        pipeline.train_runtime_conf = json_dumps(job_configuration.runtime_conf, byte=True)
        pipeline.fate_version = RuntimeConfig.get_env("FATE")
        pipeline.model_id = model_id
        pipeline.model_version = model_version

        pipeline.parent = True
        pipeline.loaded_times = 0
        pipeline.roles = json_dumps(roles, byte=True)
        pipeline.initiator_role = initiator_role
        pipeline.initiator_party_id = initiator_party_id
        pipeline.runtime_conf_on_party = json_dumps(
            runtime_conf_on_party, byte=True)
        pipeline.parent_info = json_dumps({}, byte=True)

        tracker = Tracker(job_id=job_id, role=role, party_id=party_id,
                          model_id=model_id, model_version=model_version, job_parameters=RunParameters(**job_parameters))
        tracker.save_pipeline_model(pipeline_buffer_object=pipeline)
        if role != 'local':
            tracker.save_machine_learning_model_info()
        schedule_logger(job_id).info(f"save pipeline on {role} {party_id} successfully")

    @classmethod
    def clean_job(cls, job_id, role, party_id, roles):
        schedule_logger(job_id).info(f"start to clean job on {role} {party_id}")
        # todo
        schedule_logger(job_id).info(f"job on {role} {party_id} clean done")

    @classmethod
    def job_reload(cls, job):
        schedule_logger(job.f_job_id).info(f"start job reload")
        cls.log_reload(job)
        source_inheritance_tasks, target_inheritance_tasks = cls.load_source_target_tasks(job)
        schedule_logger(job.f_job_id).info(f"source_inheritance_tasks:{source_inheritance_tasks}, target_inheritance_tasks:{target_inheritance_tasks}")
        cls.output_reload(job, source_inheritance_tasks, target_inheritance_tasks)
        cls.status_reload(job, source_inheritance_tasks, target_inheritance_tasks)

    @classmethod
    def load_source_target_tasks(cls, job):
        source_inheritance_tasks = cls.load_tasks(job_id=job.f_inheritance_info.get("job_id"), role=job.f_role,
                                                  party_id=job.f_party_id,
                                                  component_list=job.f_inheritance_info.get("component_list", []))
        target_inheritance_tasks = cls.load_tasks(job_id=job.f_job_id, role=job.f_role, party_id=job.f_party_id,
                                                  component_list=job.f_inheritance_info.get("component_list", []))
        return source_inheritance_tasks, target_inheritance_tasks

    @classmethod
    def load_tasks(cls, component_list, job_id, role, party_id):
        tasks = JobSaver.query_task(job_id=job_id, role=role, party_id=party_id, only_latest=True)
        task_dict = {}
        for cpn in component_list:
            for task in tasks:
                if cpn == task.f_component_name:
                    task_dict[cpn] = task
        return task_dict

    @classmethod
    def load_task_tracker(cls, tasks: dict):
        tracker_dict = {}
        for key, task in tasks.items():
            schedule_logger(task.f_job_id).info(
                f"task:{task.f_job_id}, {task.f_role}, {task.f_party_id},{task.f_component_name},{task.f_task_version}")
            tracker = Tracker(job_id=task.f_job_id, role=task.f_role, party_id=task.f_party_id,
                              component_name=task.f_component_name,
                              task_id=task.f_task_id,
                              task_version=task.f_task_version)
            tracker_dict[key] = tracker
        return tracker_dict

    @classmethod
    def log_reload(cls, job):
        schedule_logger(job.f_job_id).info("start reload job log")
        if job.f_inheritance_info:
            for component_name in job.f_inheritance_info.get("component_list"):
                source_path = os.path.join(log_utils.get_logger_base_dir(), job.f_inheritance_info.get("job_id"), job.f_role, job.f_party_id, component_name)
                target_path = os.path.join(log_utils.get_logger_base_dir(), job.f_job_id, job.f_role, job.f_party_id, component_name)
                if os.path.exists(source_path):
                    if os.path.exists(target_path):
                        shutil.rmtree(target_path)
                    shutil.copytree(source_path, target_path)
        schedule_logger(job.f_job_id).info("reload job log success")

    @classmethod
    def output_reload(cls, job, source_tasks: dict, target_tasks: dict):
        # model reload
        schedule_logger(job.f_job_id).info("start reload model")
        source_job = JobSaver.query_job(job_id=job.f_inheritance_info.get("job_id"))[0]
        cls.output_model_reload(job, source_job)
        cls.checkpoint_reload(job, source_job)
        schedule_logger(job.f_job_id).info("start reload data")
        source_tracker_dict = cls.load_task_tracker(source_tasks)
        target_tracker_dict = cls.load_task_tracker(target_tasks)
        for key, source_tracker in source_tracker_dict.items():
            target_tracker = target_tracker_dict[key]
            table_infos = source_tracker.get_output_data_info()
            # data reload
            schedule_logger(job.f_job_id).info(f"table infos:{table_infos}")
            for table in table_infos:
                target_tracker.log_output_data_info(data_name=table.f_data_name,
                                                    table_namespace=table.f_table_namespace,
                                                    table_name=table.f_table_name)

            # cache reload
            schedule_logger(job.f_job_id).info("start reload cache")
            cache_list = source_tracker.query_output_cache_record()
            for cache in cache_list:
                schedule_logger(job.f_job_id).info(f"start reload cache name: {cache.f_cache_name}")
                target_tracker.tracking_output_cache(cache.f_cache, cache_name=cache.f_cache_name)

            # summary reload
            schedule_logger(job.f_job_id).info("start reload summary")
            target_tracker.reload_summary(source_tracker=source_tracker)

            # metric reload
            schedule_logger(job.f_job_id).info("start reload metric")
            target_tracker.reload_metric(source_tracker=source_tracker)

        schedule_logger(job.f_job_id).info("reload output success")

    @classmethod
    def status_reload(cls, job, source_tasks, target_tasks):
        schedule_logger(job.f_job_id).info("start reload status")
        # update task status
        for key, source_task in source_tasks.items():
            JobSaver.reload_task(source_task, target_tasks[key])

        # update job status
        JobSaver.update_job(job_info={"job_id": job.f_job_id, "role": job.f_role, "party_id": job.f_party_id, "inheritance_status": JobInheritanceStatus.SUCCESS})
        schedule_logger(job.f_job_id).info("reload status success")

    @classmethod
    def output_model_reload(cls, job, source_job):
        source_model_id = model_utils.gen_party_model_id(
            source_job.f_runtime_conf.get("job_parameters").get("common").get("model_id"),
            job.f_role,
            job.f_party_id
        )
        model_id = model_utils.gen_party_model_id(
            job.f_runtime_conf.get("job_parameters").get("common").get("model_id"),
            job.f_role,
            job.f_party_id
        )
        PipelinedModel(
            model_id=model_id,
            model_version=job.f_job_id
        ).reload_component_model(
            model_id=source_model_id,
            model_version=job.f_inheritance_info.get("job_id"),
            component_list=job.f_inheritance_info.get("component_list")
        )

    @classmethod
    def checkpoint_reload(cls, job, source_job):
        for component_name in job.f_inheritance_info.get("component_list"):
            path = CheckpointManager(
                role=job.f_role,
                party_id=job.f_party_id,
                component_name=component_name,
                model_version=job.f_inheritance_info.get("job_id"),
                model_id=source_job.f_runtime_conf.get("job_parameters").get("common").get("model_id")
            ).directory
            target_path = CheckpointManager(
                role=job.f_role,
                party_id=job.f_party_id,
                component_name=component_name,
                model_version=job.f_job_id,
                model_id=job.f_runtime_conf.get("job_parameters").get("common").get("model_id")
            ).directory
            if os.path.exists(path):
                if os.path.exists(target_path):
                    shutil.rmtree(target_path)
                shutil.copytree(path, target_path)