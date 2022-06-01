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
from flask import request

from fate_flow.controller.permission_controller import PermissionController
from fate_flow.entity.permission_parameters import PermissionParameters
from fate_flow.utils import api_utils
from fate_flow.utils.api_utils import get_json_result


@manager.route('/grant', methods=['post'])
@api_utils.validate_request('party_id')
def grant_permission():
    parameters = PermissionParameters(**request.json)
    PermissionController(parameters.party_id).grant_or_delete(parameters)
    return get_json_result(retcode=0, retmsg='success')


@manager.route('/delete', methods=['post'])
@api_utils.validate_request('party_id')
def delete_permission():
    parameters = PermissionParameters(is_delete=True, **request.json)
    PermissionController(parameters.party_id).grant_or_delete(parameters)
    return get_json_result(retcode=0, retmsg='success')


@manager.route('/query', methods=['post'])
@api_utils.validate_request('party_id')
def query_privilege():
    parameters = PermissionParameters(**request.json)
    data = PermissionController(parameters.party_id).query()
    return get_json_result(retcode=0, retmsg='success', data=data)
