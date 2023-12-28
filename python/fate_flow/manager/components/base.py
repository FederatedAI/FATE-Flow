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
from fate_flow.entity.spec.dag import PartySpec, DAGSchema, DAGSpec, JobConfSpec, TaskConfSpec, TaskSpec, \
    PartyTaskSpec, PartyTaskRefSpec, RuntimeInputArtifacts
from fate_flow.manager.service.provider_manager import ProviderManager


class Base:
    @staticmethod
    def local_dag_schema(task_name, component_ref, parameters, inputs=None, provider=None, role=None, party_id=None):
        if not provider:
            provider = ProviderManager.get_fate_flow_provider()
        if not role or not party_id:
            role = "local"
            party_id = "0"
        party = PartySpec(role=role, party_id=[party_id])
        dag = DAGSchema(
            schema_version=provider.version,
            dag=DAGSpec(
                conf=JobConfSpec(task=TaskConfSpec(provider=provider.provider_name)),
                parties=[party],
                stage="default",
                tasks={task_name: TaskSpec(
                    component_ref=component_ref,
                    parties=[party],
                    conf=dict(provider=provider.provider_name)
                )},
                party_tasks={
                    f"{role}_{party_id}": PartyTaskSpec(
                        parties=[party],
                        tasks={task_name: PartyTaskRefSpec(parameters=parameters)}
                    )}
            ))
        if inputs:
            dag.dag.tasks[task_name].inputs = RuntimeInputArtifacts(**inputs)
        return dag
