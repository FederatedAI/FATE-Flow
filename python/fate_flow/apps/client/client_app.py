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

from fate_flow.apps.desc import APP_NAME, APP_ID, PARTY_ID, SITE_APP_ID, SITE_APP_TOKEN
from fate_flow.entity.code import ReturnCode
from fate_flow.entity.types import AppType
from fate_flow.manager.service.app_manager import AppManager
from fate_flow.runtime.system_settings import APP_MANAGER_PAGE
from fate_flow.utils.api_utils import API

page_name = APP_MANAGER_PAGE


@manager.route('/client/create', methods=['POST'])
@API.Input.json(app_name=fields.String(required=True), desc=APP_NAME)
def create_client_app(app_name):
    data = AppManager.create_app(app_name=app_name, app_type=AppType.CLIENT, init=False)
    return API.Output.json(code=ReturnCode.Base.SUCCESS, message="success", data=data)


@manager.route('/client/delete', methods=['POST'])
@API.Input.json(app_id=fields.String(required=True), desc=APP_ID)
def delete_client_app(app_id):
    status = AppManager.delete_app(app_id=app_id, app_type=AppType.CLIENT, init=False)
    return API.Output.json(data={"status": status})


@manager.route('/client/query', methods=['GET'])
@API.Input.params(app_id=fields.String(required=False), desc=APP_ID)
@API.Input.params(app_name=fields.String(required=False), desc=APP_NAME)
def query_client_app(app_id=None, app_name=None):
    apps = AppManager.query_app(app_id=app_id, app_name=app_name)
    return API.Output.json(code=ReturnCode.Base.SUCCESS, message="success", data=[app.to_human_model_dict() for app in apps])


@manager.route('/site/create', methods=['POST'])
@API.Input.json(party_id=fields.String(required=True), desc=PARTY_ID)
def create_site_app(party_id):
    data = AppManager.create_app(app_name=party_id, app_type=AppType.SITE)
    return API.Output.json(code=ReturnCode.Base.SUCCESS, message="success", data=data)


@manager.route('/site/delete', methods=['POST'])
@API.Input.json(party_id=fields.String(required=True), desc=PARTY_ID)
def delete_site_app(party_id):
    status = AppManager.delete_app(app_name=party_id, app_type=AppType.SITE, init=True)
    return API.Output.json(data={"status": status})


@manager.route('/site/query', methods=['GET'])
@API.Input.params(party_id=fields.String(required=True), desc=PARTY_ID)
def query_site_app(party_id=None):
    apps = AppManager.query_app(app_name=party_id, app_type=AppType.SITE,init=True)
    return API.Output.json(code=ReturnCode.Base.SUCCESS, message="success", data=[app.to_human_model_dict() for app in apps])


@manager.route('/partner/create', methods=['POST'])
@API.Input.json(party_id=fields.String(required=True), desc=PARTY_ID)
@API.Input.json(app_id=fields.String(required=True), desc=SITE_APP_ID)
@API.Input.json(app_token=fields.String(required=True), desc=SITE_APP_TOKEN)
def create_partner_app(party_id, app_id, app_token):
    data = AppManager.create_partner_app(app_id=app_id, party_id=party_id, app_token=app_token)
    return API.Output.json(code=ReturnCode.Base.SUCCESS, message="success", data=data)


@manager.route('/partner/delete', methods=['POST'])
@API.Input.json(party_id=fields.String(required=True), desc=PARTY_ID)
def delete_partner_app(party_id):
    status = AppManager.delete_partner_app(party_id=party_id, init=False)
    return API.Output.json(data={"status": status})


@manager.route('/partner/query', methods=['GET'])
@API.Input.params(party_id=fields.String(required=False), desc=PARTY_ID)
def query_partner_app(party_id=None):
    apps = AppManager.query_partner_app(party_id=party_id)
    return API.Output.json(code=ReturnCode.Base.SUCCESS, message="success", data=[app.to_human_model_dict() for app in apps])
