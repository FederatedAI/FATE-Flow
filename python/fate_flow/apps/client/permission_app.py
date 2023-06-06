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
from fate_flow.runtime.runtime_config import RuntimeConfig
from fate_flow.runtime.system_settings import PERMISSION_MANAGER_PAGE
from fate_flow.utils.api_utils import API

page_name = PERMISSION_MANAGER_PAGE


@manager.route('/grant', methods=['POST'])
@API.Input.json(app_id=fields.String(required=True))
@API.Input.json(role=fields.String(required=True))
def grant(app_id, role):
    status = PermissionController.add_role_for_user(app_id=app_id, role=role)
    return API.Output.json(data={"status": status})


@manager.route('/delete', methods=['POST'])
@API.Input.json(app_id=fields.String(required=True))
@API.Input.json(role=fields.String(required=True))
def delete(app_id, role):
    status = PermissionController.delete_role_for_user(app_id=app_id, role=role)
    return API.Output.json(data={"status": status})


@manager.route('/query', methods=['GET'])
@API.Input.params(app_id=fields.String(required=True))
def query(app_id):
    permissions = {}
    for role in PermissionController.get_roles_for_user(app_id=app_id):
        permissions[role] = PermissionController.get_permissions_for_user(app_id=role)
    return API.Output.json(code=ReturnCode.Base.SUCCESS, data=permissions)


@manager.route('/role/query', methods=['GET'])
def query_roles():
    return API.Output.json(data=RuntimeConfig.CLIENT_ROLE)