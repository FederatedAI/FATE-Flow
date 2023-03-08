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
from webargs import fields

from fate_flow.controller.app_controller import PermissionController
from fate_flow.entity.code import ReturnCode
from fate_flow.settings import PERMISSION_PAGE
from fate_flow.utils.api_utils import get_json_result, validate_request_json, validate_request_params

page_name = PERMISSION_PAGE


@manager.route('/app/grant', methods=['POST'])
@validate_request_json(app_id=fields.String(required=True), role=fields.String(required=True))
def grant(app_id, role):
    PermissionController.add_role_for_user(app_id=app_id, role=role)
    return get_json_result(code=ReturnCode.Base.SUCCESS)


@manager.route('/app/delete', methods=['POST'])
@validate_request_json(app_id=fields.String(required=True), role=fields.String(required=True))
def delete(app_id, role):
    PermissionController.delete_role_for_user(app_id=app_id, role=role)
    return get_json_result(code=ReturnCode.Base.SUCCESS)


@manager.route('/app/query', methods=['GET'])
@validate_request_params(app_id=fields.String(required=True))
def query(app_id):
    roles = PermissionController.get_roles_for_user(app_id=app_id)
    permissions = PermissionController.get_permissions_for_user(app_id=app_id)
    return get_json_result(code=ReturnCode.Base.SUCCESS, data={"roles": roles, "permission": permissions})
