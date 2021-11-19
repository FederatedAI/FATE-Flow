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
from fate_flow.db.service_registry import ServiceRegistry
from fate_flow.db.config_manager import ConfigManager
from fate_flow.db.job_default_config import JobDefaultConfig
from fate_flow.entity import RetCode

@manager.route('/version/get', methods=['POST'])
def get_fate_version_info():
    module = request.json.get('module', None)
    if module:
        version = {module: RuntimeConfig.get_env(module)}
    else:
        version = RuntimeConfig.get_all_env()
    version["API"] = API_VERSION
    return get_json_result(data=version)


@manager.route('/service/get', methods=['POST'])
def get_service_registry():
    return get_json_result(data=ServiceRegistry.get_all())


@manager.route('/service/<service_name>/register', methods=['POST'])
def register_service(service_name: str):
    ServiceRegistry.register(service_name.upper(), request.json)
    if ServiceRegistry.get(service_name) is not None:
        return get_json_result()
    else:
        return get_json_result(retcode=RetCode.OPERATING_ERROR)


@manager.route('/service/<service_name>/get', methods=['POST'])
def get_service(service_name: str):
    return get_json_result(data=ServiceRegistry.get(service_name.upper()))


@manager.route('/reload', methods=['POST'])
def reload():
    config = ConfigManager.load()
    return get_json_result(data=config)


@manager.route('/config/job/default', methods=['POST'])
def job_default_config():
    return get_json_result(data=JobDefaultConfig.get_all())
