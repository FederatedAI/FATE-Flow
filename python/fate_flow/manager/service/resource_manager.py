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
from pydantic import typing

from fate_flow.db.base_models import DB
from fate_flow.db.db_models import EngineRegistry, Job, Task
from fate_flow.entity.types import EngineType, ResourceOperation, LauncherType
from fate_flow.runtime.job_default_config import JobDefaultConfig
from fate_flow.runtime.system_settings import IGNORE_RESOURCE_ROLES, ENGINES
from fate_flow.utils import engine_utils, base_utils, job_utils
from fate_flow.utils.log import getLogger
from fate_flow.utils.log_utils import schedule_logger

stat_logger = getLogger()


class ResourceManager(object):
    @classmethod
    def initialize(cls):
        engines_config = engine_utils.get_engines_config_from_conf(group_map=True)
        for engine_type, engine_configs in engines_config.items():
            for engine_name, engine_config in engine_configs.items():
                cls.register_engine(engine_type=engine_type, engine_name=engine_name, engine_config=engine_config)

    @classmethod
    @DB.connection_context()
    def register_engine(cls, engine_type, engine_name, engine_config):
        cores = engine_config.get("cores", 0)
        memory = engine_config.get("memory", 0)
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
            operate = EngineRegistry.update(update_fields).where(*filters)
            update_status = operate.execute() > 0
            if update_status:
                stat_logger.info(f"update {engine_type} engine {engine_name} registration information")
            else:
                stat_logger.info(f"update {engine_type} engine {engine_name} registration information takes no effect")
        else:
            resource = EngineRegistry()
            resource.f_create_time = base_utils.current_timestamp()
            resource.f_engine_type = engine_type
            resource.f_engine_name = engine_name
            resource.f_engine_config = engine_config

            resource.f_cores = cores
            resource.f_memory = memory
            resource.f_remaining_cores = cores
            resource.f_remaining_memory = memory
            try:
                resource.save(force_insert=True)
            except Exception as e:
                stat_logger.warning(e)
            stat_logger.info(f"create {engine_type} engine {engine_name} registration information")

    @classmethod
    def apply_for_job_resource(cls, job_id, role, party_id):
        return cls.resource_for_job(job_id=job_id, role=role, party_id=party_id, operation_type=ResourceOperation.APPLY)

    @classmethod
    def return_job_resource(cls, job_id, role, party_id):
        return cls.resource_for_job(job_id=job_id, role=role, party_id=party_id,
                                    operation_type=ResourceOperation.RETURN)

    @classmethod
    @DB.connection_context()
    def resource_for_job(cls, job_id, role, party_id, operation_type: ResourceOperation):
        operate_status = False
        cores, memory = cls.query_job_resource(job_id=job_id, role=role, party_id=party_id)
        engine_name = ENGINES.get(EngineType.COMPUTING)
        try:
            with DB.atomic():
                updates = {
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
    def apply_for_task_resource(cls, **task_info):
        return ResourceManager.resource_for_task(task_info=task_info, operation_type=ResourceOperation.APPLY)

    @classmethod
    def return_task_resource(cls, **task_info):
        return ResourceManager.resource_for_task(task_info=task_info, operation_type=ResourceOperation.RETURN)

    @classmethod
    @DB.connection_context()
    def resource_for_task(cls, task_info, operation_type):
        cores_per_task, memory_per_task = cls.query_task_resource(task_info=task_info)
        schedule_logger(task_info["job_id"]).info(f"{operation_type} cores_per_task:{cores_per_task}, memory_per_task:{memory_per_task}")
        operate_status = False
        if cores_per_task or memory_per_task:
            try:
                with DB.atomic():
                    updates = {}
                    filters = [
                        Task.f_job_id == task_info["job_id"],
                        Task.f_role == task_info["role"],
                        Task.f_party_id == task_info["party_id"],
                        Task.f_task_id == task_info["task_id"],
                        Task.f_task_version == task_info["task_version"]
                    ]
                    if operation_type is ResourceOperation.APPLY:
                        updates[Task.f_resource_in_use] = True
                        filters.append(Task.f_resource_in_use == False)
                    elif operation_type is ResourceOperation.RETURN:
                        updates[Task.f_resource_in_use] = False
                        filters.append(Task.f_resource_in_use == True)
                    operate = Task.update(updates).where(*filters)
                    record_status = operate.execute() > 0
                    if not record_status:
                        raise RuntimeError(f"record task {task_info['task_id']} {task_info['task_version']} resource"
                                           f"{operation_type} failed on {task_info['role']} {task_info['party_id']}")
                    filters, updates = cls.update_resource_sql(resource_model=Job,
                                                               cores=cores_per_task,
                                                               memory=memory_per_task,
                                                               operation_type=operation_type,
                                                               )
                    filters.append(Job.f_job_id == task_info["job_id"])
                    filters.append(Job.f_role == task_info["role"])
                    filters.append(Job.f_party_id == task_info["party_id"])
                    # filters.append(Job.f_resource_in_use == True)
                    operate = Job.update(updates).where(*filters)
                    operate_status = operate.execute() > 0
                    if not operate_status:
                        raise RuntimeError(f"record task {task_info['task_id']} {task_info['task_version']} job resource "
                                           f"{operation_type} failed on {task_info['role']} {task_info['party_id']}")
            except Exception as e:
                schedule_logger(task_info["job_id"]).warning(e)
                operate_status = False
        else:
            operate_status = True
        if operate_status:
            schedule_logger(task_info["job_id"]).info(
                "task {} {} {} {} {} resource successfully".format(
                    task_info["role"],
                    task_info["party_id"],
                    task_info["task_id"],
                    task_info["task_version"],
                    operation_type))
        else:
            schedule_logger(task_info["job_id"]).warning(
                "task {} {} {} resource failed".format(
                    task_info["task_id"],
                    task_info["task_version"], operation_type))
        return operate_status

    @classmethod
    def query_job_resource(cls, job_id, role, party_id):
        cores, memory = job_utils.get_job_resource_info(job_id, role, party_id)
        return int(cores), memory

    @classmethod
    def query_task_resource(cls, task_info: dict = None):
        cores_per_task = 0
        memory_per_task = 0
        if task_info["role"] in IGNORE_RESOURCE_ROLES:
            return cores_per_task, memory_per_task
        task_cores, memory, launcher_name = job_utils.get_task_resource_info(
            task_info["job_id"], task_info["role"], task_info["party_id"], task_info["task_id"], task_info["task_version"]
        )
        if launcher_name == LauncherType.DEEPSPEED:
            # todo: apply gpus
            return 0, 0
        return task_cores, memory

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
            filters = [
                resource_model.f_remaining_cores + cores <= resource_model.f_cores
            ]
            updates = {resource_model.f_remaining_cores: resource_model.f_remaining_cores + cores,
                       resource_model.f_remaining_memory: resource_model.f_remaining_memory + memory}
        else:
            raise RuntimeError(f"can not support {operation_type} resource operation type")
        return filters, updates

    @classmethod
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
