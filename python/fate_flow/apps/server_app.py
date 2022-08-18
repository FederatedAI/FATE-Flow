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

from fate_flow.db.runtime_config import RuntimeConfig
from fate_flow.utils.api_utils import get_json_result
from fate_flow.settings import API_VERSION
from fate_flow.db.service_registry import ServerRegistry
from fate_flow.db.config_manager import ConfigManager
from fate_flow.db.job_default_config import JobDefaultConfig
from fate_flow.entity import RetCode


@manager.route('/fateflow/info', methods=['POST'])
def fate_flow_server_info():
    data = RuntimeConfig.SERVICE_DB.get_servers()
    return get_json_result(data=data)


@manager.route('/version/get', methods=['POST'])
def get_fate_version_info():
    module = (request.json or {}).get('module', None)
    if module:
        version = {module: RuntimeConfig.get_env(module)}
    else:
        version = RuntimeConfig.get_all_env()
    version["API"] = API_VERSION
    return get_json_result(data=version)


@manager.route('/get', methods=['POST'])
@manager.route('/service/get', methods=['POST'])
def get_server_registry():
    return get_json_result(data=ServerRegistry.get_all())


@manager.route('/<server_name>/register', methods=['POST'])
@manager.route('/service/<server_name>/register', methods=['POST'])
def register_server(server_name: str):
    ServerRegistry.register(server_name.upper(), request.json)
    if ServerRegistry.get(server_name.upper()) is not None:
        return get_json_result()
    else:
        return get_json_result(retcode=RetCode.OPERATING_ERROR)


@manager.route('/<server_name>/get', methods=['POST'])
@manager.route('/service/<server_name>/get', methods=['POST'])
def get_server(server_name: str):
    return get_json_result(data=ServerRegistry.get(server_name.upper()))


@manager.route('/reload', methods=['POST'])
def reload():
    config = ConfigManager.load()
    return get_json_result(data=config)


@manager.route('/config/job/default', methods=['POST'])
def job_default_config():
    return get_json_result(data=JobDefaultConfig.get_all())
