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
from fate_flow.db.base_models import DB
from fate_flow.db.db_models import EngineRegistry
from fate_flow.entity.types import ResourceOperation
from fate_flow.utils import engine_utils


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
        cores = engine_config.get("cores_per_node", 0) * nodes
        memory = engine_config.get("memory_per_node", 0) * nodes
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


    @classmethod
    def apply_for_job_resource(cls, job_id, role, party_id):
        return cls.resource_for_job(job_id=job_id, role=role, party_id=party_id, operation_type=ResourceOperation.APPLY)

    @classmethod
    def return_job_resource(cls, job_id, role, party_id):
        return cls.resource_for_job(job_id=job_id, role=role, party_id=party_id,
                                    operation_type=ResourceOperation.RETURN)

    @classmethod
    def resource_for_job(cls, job_id, role, party_id, operation_type: ResourceOperation):
        return True

    @classmethod
    def apply_for_task_resource(cls, task_info):
        return ResourceManager.resource_for_task(task_info=task_info, operation_type=ResourceOperation.APPLY)

    @classmethod
    def return_task_resource(cls, task_info):
        # todo
        return ResourceManager.resource_for_task(task_info=task_info, operation_type=ResourceOperation.RETURN)

    @classmethod
    def resource_for_task(cls, task_info, operation_type):
        # todo
        return
