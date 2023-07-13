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
from fate_flow.entity.spec.dag import DAGSchema
from fate_flow.hook.common.parameters import PermissionCheckParameters
from fate_flow.hub.flow_hub import FlowHub


def get_permission_parameters(role, party_id, initiator_party_id, job_info) -> PermissionCheckParameters:
    dag_schema = DAGSchema(**job_info['dag_schema'])
    job_parser = FlowHub.load_job_parser(dag_schema)
    component_list = job_parser.component_ref_list(role, party_id)
    dataset_list = job_parser.dataset_list(role, party_id)
    component_parameters = job_parser.role_parameters(role, party_id)
    return PermissionCheckParameters(
        initiator_party_id=initiator_party_id,
        roles=dag_schema.dag.parties,
        component_list=component_list,
        dataset_list=dataset_list,
        dag_schema=dag_schema.dict(),
        component_parameters=component_parameters
    )
