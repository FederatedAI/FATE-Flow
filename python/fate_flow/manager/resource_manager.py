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
import math
import typing

from fate_arch.common import EngineType
from fate_arch.common import base_utils
from fate_flow.utils.log_utils import schedule_logger
from fate_arch.computing import ComputingEngine
from fate_arch.common import engine_utils
from fate_flow.db.db_models import DB, EngineRegistry, Job
from fate_flow.entity.types import ResourceOperation
from fate_flow.entity import RunParameters
from fate_flow.operation.job_saver import JobSaver
from fate_flow.settings import stat_logger, IGNORE_RESOURCE_ROLES, SUPPORT_IGNORE_RESOURCE_ENGINES, \
    IGNORE_RESOURCE_COMPUTING_ENGINE, ENGINES
from fate_flow.utils import job_utils
from fate_flow.db.job_default_config import JobDefaultConfig


class ResourceManager(object):
    @classmethod
    def initialize(cls):
        engines_config, engine_group_map = engine_utils.get_engines_config_from_conf(group_map=True)
        for engine_type, engine_configs in engines_config.items():
            for engine_name, engine_config in engine_configs.items():
                cls.register_engine(engine_type=engine_type, engine_name=engine_name, engine_entrance=engine_group_map[engine_type][engine_name], engine_config=engine_config)

    @classmethod
    @DB.connection_context()
    def register_engine(cls, engine_type, engine_name, engine_entrance, engine_config):
        nodes = engine_config.get("nodes", 1)
        cores = engine_config.get("cores_per_node", 0) * nodes * JobDefaultConfig.total_cores_overweight_percent
        memory = engine_config.get("memory_per_node", 0) * nodes * JobDefaultConfig.total_memory_overweight_percent
        filters = [EngineRegistry.f_engine_type == engine_type, EngineRegistry.f_engine_name == engine_name]
        resources = EngineRegistry.select().where(*filters)
        if resources:
            resource = resources[0]
            update_fields = {}
            update_fields[EngineRegistry.f_engine_config] = engine_config
            update_fields[EngineRegistry.f_cores] = cores
            update_fields[EngineRegistry.f_memory] = memory
            update_fields[EngineRegistry.f_remaining_cores] = EngineRegistry.f_remaining_cores + (
                    cores - resource.f_cores)
            update_fields[EngineRegistry.f_remaining_memory] = EngineRegistry.f_remaining_memory + (
                    memory - resource.f_memory)
            update_fields[EngineRegistry.f_nodes] = nodes
            operate = EngineRegistry.update(update_fields).where(*filters)
            update_status = operate.execute() > 0
            if update_status:
                stat_logger.info(f"update {engine_type} engine {engine_name} {engine_entrance} registration information")
            else:
                stat_logger.info(f"update {engine_type} engine {engine_name} {engine_entrance} registration information takes no effect")
        else:
            resource = EngineRegistry()
            resource.f_create_time = base_utils.current_timestamp()
            resource.f_engine_type = engine_type
            resource.f_engine_name = engine_name
            resource.f_engine_entrance = engine_entrance
            resource.f_engine_config = engine_config

            resource.f_cores = cores
            resource.f_memory = memory
            resource.f_remaining_cores = cores
            resource.f_remaining_memory = memory
            resource.f_nodes = nodes
            try:
                resource.save(force_insert=True)
            except Exception as e:
                stat_logger.warning(e)
            stat_logger.info(f"create {engine_type} engine {engine_name} {engine_entrance} registration information")

    @classmethod
    def check_resource_apply(cls, job_parameters: RunParameters, role, party_id, engines_info):
        computing_engine, cores, memory = cls.calculate_job_resource(job_parameters=job_parameters, role=role, party_id=party_id)
        max_cores_per_job = math.floor(engines_info[EngineType.COMPUTING].f_cores * JobDefaultConfig.max_cores_percent_per_job) \
            if engines_info.get(EngineType.COMPUTING) else 0

        if cores > max_cores_per_job:
            return False, cores, max_cores_per_job
        return True, cores, max_cores_per_job

    @classmethod
    def apply_for_job_resource(cls, job_id, role, party_id):
        return cls.resource_for_job(job_id=job_id, role=role, party_id=party_id, operation_type=ResourceOperation.APPLY)

    @classmethod
    def return_job_resource(cls, job_id, role, party_id):
        return cls.resource_for_job(job_id=job_id, role=role, party_id=party_id,
                                    operation_type=ResourceOperation.RETURN)

    @classmethod
    def query_resource(cls, resource_in_use=True, engine_name=None):
        if not engine_name:
            engine_name = ENGINES.get(EngineType.COMPUTING)
        use_resource_jobs = JobSaver.query_job(resource_in_use=resource_in_use)
        used = []
        for job in use_resource_jobs:
            used.append({"job_id": job.f_job_id, "role": job.f_role, "party_id": job.f_party_id,
                         "core": job.f_cores, "memory": job.f_memory})
        computing_engine_resource = cls.get_engine_registration_info(engine_type=EngineType.COMPUTING, engine_name=engine_name)
        return used, computing_engine_resource.to_dict() if computing_engine_resource else {}

    @classmethod
    def return_resource(cls, job_id):
        jobs = JobSaver.query_job(job_id=job_id)
        if not jobs:
            raise Exception(f'no found job {job_id}')
        return_resource_job_list = []
        for job in jobs:
            job_info = {"job_id": job.f_job_id, "role": job.f_role, "party_id": job.f_party_id,
                        "resource_in_use": job.f_resource_in_use, "resource_return_status": False}
            if job.f_resource_in_use:
                return_status = cls.return_job_resource(job.f_job_id, job.f_role, job.f_party_id)
                job_info["resource_return_status"] = return_status
            return_resource_job_list.append(job_info)
        return return_resource_job_list

    @classmethod
    @DB.connection_context()
    def resource_for_job(cls, job_id, role, party_id, operation_type: ResourceOperation):
        operate_status = False
        engine_name, cores, memory = cls.calculate_job_resource(job_id=job_id, role=role, party_id=party_id)
        try:
            with DB.atomic():
                updates = {
                    Job.f_engine_type: EngineType.COMPUTING,
                    Job.f_engine_name: engine_name,
                    Job.f_cores: cores,
                    Job.f_memory: memory,
                }
                filters = [
                    Job.f_job_id == job_id,
                    Job.f_role == role,
                    Job.f_party_id == party_id,
                ]
                if operation_type is ResourceOperation.APPLY:
                    updates[Job.f_remaining_cores] = cores
                    updates[Job.f_remaining_memory] = memory
                    updates[Job.f_resource_in_use] = True
                    updates[Job.f_apply_resource_time] = base_utils.current_timestamp()
                    filters.append(Job.f_resource_in_use == False)
                elif operation_type is ResourceOperation.RETURN:
                    updates[Job.f_resource_in_use] = False
                    updates[Job.f_return_resource_time] = base_utils.current_timestamp()
                    filters.append(Job.f_resource_in_use == True)
                operate = Job.update(updates).where(*filters)
                record_status = operate.execute() > 0
                if not record_status:
                    raise RuntimeError(f"record job {job_id} resource {operation_type} failed on {role} {party_id}")

                if cores or memory:
                    filters, updates = cls.update_resource_sql(resource_model=EngineRegistry,
                                                               cores=cores,
                                                               memory=memory,
                                                               operation_type=operation_type,
                                                               )
                    filters.append(EngineRegistry.f_engine_type == EngineType.COMPUTING)
                    filters.append(EngineRegistry.f_engine_name == engine_name)
                    operate = EngineRegistry.update(updates).where(*filters)
                    apply_status = operate.execute() > 0
                else:
                    apply_status = True
                if not apply_status:
                    raise RuntimeError(
                        f"update engine {engine_name} record for job {job_id} resource {operation_type} on {role} {party_id} failed")
            operate_status = True
        except Exception as e:
            schedule_logger(job_id).warning(e)
            schedule_logger(job_id).warning(
                f"{operation_type} job resource(cores {cores} memory {memory}) on {role} {party_id} failed")
            operate_status = False
        finally:
            remaining_cores, remaining_memory = cls.get_remaining_resource(EngineRegistry,
                                                                           [
                                                                               EngineRegistry.f_engine_type == EngineType.COMPUTING,
                                                                               EngineRegistry.f_engine_name == engine_name])
            operate_msg = "successfully" if operate_status else "failed"
            schedule_logger(job_id).info(
                f"{operation_type} job resource(cores {cores} memory {memory}) on {role} {party_id} {operate_msg}, remaining cores: {remaining_cores} remaining memory: {remaining_memory}")
            return operate_status

    @classmethod
    def adapt_engine_parameters(cls, role, job_parameters: RunParameters, create_initiator_baseline=False):
        computing_engine_info = ResourceManager.get_engine_registration_info(engine_type=EngineType.COMPUTING,
                                                                             engine_name=job_parameters.computing_engine)
        if not job_parameters.adaptation_parameters or create_initiator_baseline:
            job_parameters.adaptation_parameters = {
                "task_nodes": 0,
                "task_cores_per_node": 0,
                "task_memory_per_node": 0,
                # request_task_cores base on initiator and distribute to all parties, using job conf parameters or initiator fateflow server default settings
                "request_task_cores": int(job_parameters.task_cores) if job_parameters.task_cores else JobDefaultConfig.task_cores,
                "if_initiator_baseline": True
            }
        else:
            # use initiator baseline
            if role == "arbiter":
                job_parameters.adaptation_parameters["request_task_cores"] = 1
            elif "request_task_cores" not in job_parameters.adaptation_parameters:
                # compatibility 1.5.0
                job_parameters.adaptation_parameters["request_task_cores"] = job_parameters.adaptation_parameters["task_nodes"] * job_parameters.adaptation_parameters["task_cores_per_node"]

            job_parameters.adaptation_parameters["if_initiator_baseline"] = False
        adaptation_parameters = job_parameters.adaptation_parameters

        if job_parameters.computing_engine in {ComputingEngine.STANDALONE, ComputingEngine.EGGROLL}:
            adaptation_parameters["task_nodes"] = computing_engine_info.f_nodes
            if int(job_parameters.eggroll_run.get("eggroll.session.processors.per.node", 0)) > 0:
                adaptation_parameters["task_cores_per_node"] = int(job_parameters.eggroll_run["eggroll.session.processors.per.node"])
            else:
                adaptation_parameters["task_cores_per_node"] = max(1, int(adaptation_parameters["request_task_cores"] / adaptation_parameters["task_nodes"]))
            if not create_initiator_baseline:
                # set the adaptation parameters to the actual engine operation parameters
                job_parameters.eggroll_run["eggroll.session.processors.per.node"] = adaptation_parameters["task_cores_per_node"]
        elif job_parameters.computing_engine == ComputingEngine.SPARK or job_parameters.computing_engine == ComputingEngine.LINKIS_SPARK:
            adaptation_parameters["task_nodes"] = int(job_parameters.spark_run.get("num-executors", computing_engine_info.f_nodes))
            if int(job_parameters.spark_run.get("executor-cores", 0)) > 0:
                adaptation_parameters["task_cores_per_node"] = int(job_parameters.spark_run["executor-cores"])
            else:
                adaptation_parameters["task_cores_per_node"] = max(1, int(adaptation_parameters["request_task_cores"] / adaptation_parameters["task_nodes"]))
            if not create_initiator_baseline:
                # set the adaptation parameters to the actual engine operation parameters
                job_parameters.spark_run["num-executors"] = adaptation_parameters["task_nodes"]
                job_parameters.spark_run["executor-cores"] = adaptation_parameters["task_cores_per_node"]

    @classmethod
    def calculate_job_resource(cls, job_parameters: RunParameters = None, job_id=None, role=None, party_id=None):
        if not job_parameters:
            job_parameters = job_utils.get_job_parameters(job_id=job_id,
                                                          role=role,
                                                          party_id=party_id)
            job_parameters = RunParameters(**job_parameters)

        cores = 0
        memory = 0

        if not (job_parameters.computing_engine in IGNORE_RESOURCE_COMPUTING_ENGINE or
                role in IGNORE_RESOURCE_ROLES and job_parameters.computing_engine in SUPPORT_IGNORE_RESOURCE_ENGINES):
            cores = (int(job_parameters.adaptation_parameters["task_cores_per_node"] or 0) *
                     int(job_parameters.adaptation_parameters["task_nodes"] or 0) *
                     int(job_parameters.task_parallelism or 0))
            memory = (int(job_parameters.adaptation_parameters["task_memory_per_node"] or 0) *
                      int(job_parameters.adaptation_parameters["task_nodes"] or 0) *
                      int(job_parameters.task_parallelism or 0))

        return job_parameters.computing_engine, cores, memory

    @classmethod
    def calculate_task_resource(cls, task_parameters: RunParameters = None, task_info: dict = None):
        if not task_parameters:
            job_parameters = job_utils.get_job_parameters(job_id=task_info["job_id"],
                                                          role=task_info["role"],
                                                          party_id=task_info["party_id"])
            task_parameters = RunParameters(**job_parameters)
        if task_parameters.computing_engine in IGNORE_RESOURCE_COMPUTING_ENGINE:
            cores_per_task = 0
            memory_per_task = 0
        elif task_info["role"] in IGNORE_RESOURCE_ROLES and task_parameters.computing_engine in SUPPORT_IGNORE_RESOURCE_ENGINES:
            cores_per_task = 0
            memory_per_task = 0
        else:
            cores_per_task = task_parameters.adaptation_parameters["task_cores_per_node"] * \
                             task_parameters.adaptation_parameters["task_nodes"]
            memory_per_task = task_parameters.adaptation_parameters["task_memory_per_node"] * \
                              task_parameters.adaptation_parameters["task_nodes"]
        return cores_per_task, memory_per_task

    @classmethod
    def apply_for_task_resource(cls, task_info):
        return ResourceManager.resource_for_task(task_info=task_info, operation_type=ResourceOperation.APPLY)

    @classmethod
    def return_task_resource(cls, task_info):
        return ResourceManager.resource_for_task(task_info=task_info, operation_type=ResourceOperation.RETURN)

    @classmethod
    @DB.connection_context()
    def resource_for_task(cls, task_info, operation_type):
        cores_per_task, memory_per_task = cls.calculate_task_resource(task_info=task_info)
        schedule_logger(task_info["job_id"]).info(f"cores_per_task:{cores_per_task}, memory_per_task:{memory_per_task}")
        if cores_per_task or memory_per_task:
            filters, updates = cls.update_resource_sql(resource_model=Job,
                                                       cores=cores_per_task,
                                                       memory=memory_per_task,
                                                       operation_type=operation_type,
                                                       )
            filters.append(Job.f_job_id == task_info["job_id"])
            filters.append(Job.f_role == task_info["role"])
            filters.append(Job.f_party_id == task_info["party_id"])
            filters.append(Job.f_resource_in_use == True)
            operate = Job.update(updates).where(*filters)
            operate_status = operate.execute() > 0
        else:
            operate_status = True
        if operate_status:
            schedule_logger(task_info["job_id"]).info(
                "task {} {} {} resource successfully".format(task_info["task_id"],
                                                             task_info["task_version"], operation_type))
        else:
            schedule_logger(task_info["job_id"]).warning(
                "task {} {} {} resource failed".format(task_info["task_id"],
                                                       task_info["task_version"], operation_type))
        return operate_status

    @classmethod
    def update_resource_sql(cls, resource_model: typing.Union[EngineRegistry, Job], cores, memory, operation_type: ResourceOperation):
        if operation_type is ResourceOperation.APPLY:
            filters = [
                resource_model.f_remaining_cores >= cores,
                resource_model.f_remaining_memory >= memory
            ]
            updates = {resource_model.f_remaining_cores: resource_model.f_remaining_cores - cores,
                       resource_model.f_remaining_memory: resource_model.f_remaining_memory - memory}
        elif operation_type is ResourceOperation.RETURN:
            filters = []
            updates = {resource_model.f_remaining_cores: resource_model.f_remaining_cores + cores,
                       resource_model.f_remaining_memory: resource_model.f_remaining_memory + memory}
        else:
            raise RuntimeError(f"can not support {operation_type} resource operation type")
        return filters, updates

    @classmethod
    @DB.connection_context()
    def get_remaining_resource(cls, resource_model: typing.Union[EngineRegistry, Job], filters):
        remaining_cores, remaining_memory = None, None
        try:
            objs = resource_model.select(resource_model.f_remaining_cores, resource_model.f_remaining_memory).where(
                *filters)
            if objs:
                remaining_cores, remaining_memory = objs[0].f_remaining_cores, objs[0].f_remaining_memory
        except Exception as e:
            schedule_logger().exception(e)
        finally:
            return remaining_cores, remaining_memory

    @classmethod
    @DB.connection_context()
    def get_engine_registration_info(cls, engine_type, engine_name) -> EngineRegistry:
        engines = EngineRegistry.select().where(EngineRegistry.f_engine_type == engine_type,
                                                EngineRegistry.f_engine_name == engine_name)
        if engines:
            return engines[0]
