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
from functools import wraps
from flask import request as flask_request

from fate_flow.controller.parser import JobParser
from fate_flow.entity.code import ReturnCode
from fate_flow.entity.spec.dag import DAGSchema
from fate_flow.hook import HookManager
from fate_flow.hook.common.parameters import PermissionCheckParameters
from fate_flow.manager.service.provider_manager import ProviderManager
from fate_flow.runtime.system_settings import PERMISSION_SWITCH
from fate_flow.utils.api_utils import API


def get_permission_parameters(role, party_id, initiator_party_id, job_info) -> PermissionCheckParameters:
    dag_schema = DAGSchema(**job_info)
    job_parser = JobParser(dag_schema)
    component_list = job_parser.component_ref_list(role, party_id)
    fate_component_list = set(component_list) - set(ProviderManager.get_flow_components())
    dataset_list = job_parser.dataset_list(role, party_id)
    component_parameters = job_parser.role_parameters(role, party_id)
    return PermissionCheckParameters(
        initiator_party_id=initiator_party_id,
        roles=dag_schema.dag.parties,
        component_list=fate_component_list,
        dataset_list=dataset_list,
        dag_schema=dag_schema.dict(),
        component_parameters=component_parameters
    )


def create_job_request_check(func):
    @wraps(func)
    def _wrapper(*_args, **_kwargs):
        party_id = _kwargs.get("party_id")
        role = _kwargs.get("role")
        body = flask_request.json
        headers = flask_request.headers
        initiator_party_id = headers.get("initiator_party_id")

        # permission check
        if PERMISSION_SWITCH:
            permission_return = HookManager.permission_check(get_permission_parameters(
                role, party_id, initiator_party_id, body
            ))
            if permission_return.code != ReturnCode.Base.SUCCESS:
                return API.Output.fate_flow_exception(permission_return)
        return func(*_args, **_kwargs)
    return _wrapper
