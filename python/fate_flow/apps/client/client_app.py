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

from fate_flow.entity.code import ReturnCode
from fate_flow.manager.app_manager import AppManager
from fate_flow.utils.api_utils import validate_request_params, validate_request_json, get_json_result


@manager.route('/app/create', methods=['POST'])
@validate_request_json(app_name=fields.String(required=True))
def create_app(app_name):
    data = AppManager.create_app(app_name=app_name)
    return get_json_result(code=ReturnCode.Base.SUCCESS, message="success", data=data)


@manager.route('/app/delete', methods=['POST'])
@validate_request_json(app_id=fields.String(required=True))
def delete_app(app_id):
    data = AppManager.delete_app(app_id=app_id)
    return get_json_result(code=ReturnCode.Base.SUCCESS, message="success", data=data)


@manager.route('/app/query', methods=['GET'])
@validate_request_params(app_id=fields.String(required=False), app_name=fields.String(required=False))
def query_app(app_id=None, app_name=None):
    apps = AppManager.query_app(app_id=app_id, app_name=app_name)
    return get_json_result(code=ReturnCode.Base.SUCCESS, message="success", data=[app.to_human_model_dict() for app in apps])
