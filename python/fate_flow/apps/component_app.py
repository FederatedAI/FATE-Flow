#
#  Copyright 2021 The FATE Authors. All Rights Reserved.
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

from fate_arch.common.file_utils import get_federatedml_setting_conf_directory
from fate_flow.utils.api_utils import error_response, get_json_result
from fate_flow.utils.detect_utils import check_config
from fate_flow.scheduler.dsl_parser import DSLParser, DSLParserV2
from fate_flow.utils.api_utils import get_json_result
from fate_flow.utils.detect_utils import validate_request
from fate_flow.db.component_registry import ComponentRegistry
from fate_flow.entity.component_provider import ComponentProvider
from fate_flow.entity.retcode import RetCode
from fate_flow.manager.provider_manager import ProviderManager


@manager.route('/registry/get', methods=['POST'])
def get_registry():
    return get_json_result(data=ComponentRegistry.REGISTRY)

@manager.route('/provider/register', methods=['POST'])
@validate_request("name", "version", "path")
def register():
    info = request.json or request.form.to_dict()
    provider = ComponentProvider(name=info["name"],
                                 version=info["version"],
                                 path=info["path"],
                                 class_path=info.get("class_path", ComponentRegistry.get_default_class_path()))
    code, std = ProviderManager.start_registrar_process(provider=provider)
    if code == 0:
        ComponentRegistry.load()
        if ComponentRegistry.get_providers().get(provider.name, {}).get(provider.version, None) is None:
            return get_json_result(retcode=RetCode.OPERATING_ERROR, retmsg=f"not load into memory")
        else:
            return get_json_result()
    else:
        return get_json_result(retcode=RetCode.OPERATING_ERROR, retmsg=f"register failed:\n{std}")

@manager.route('/provider/get', methods=['POST'])
def get_providers():
    return get_json_result(data=ComponentRegistry.get_providers())

@manager.route('/provider/<provider_name>/get', methods=['POST'])
def get_provider(provider_name):
    return get_json_result(data=ComponentRegistry.get_providers().get(provider_name))


@manager.route('/get', methods=['POST'])
def get_components():
    return get_json_result(data=ComponentRegistry.get_components())

@manager.route('/<component_name>/get', methods=['POST'])
def get_component(component_name):
    return get_json_result(data=ComponentRegistry.get_components().get(component_name))

@manager.route('/validate', methods=['POST'])
def validate_component_param():
    if not request.json or not isinstance(request.json, dict):
        return error_response(400, 'bad request')

    required_keys = [
        'component_name',
        'component_module_name',
    ]
    config_keys = ['role']

    dsl_version = int(request.json.get('dsl_version', 0))
    if dsl_version == 1:
        config_keys += ['role_parameters', 'algorithm_parameters']
        parser_class = DSLParser
    elif dsl_version == 2:
        config_keys += ['component_parameters']
        parser_class = DSLParserV2
    else:
        return error_response(400, 'unsupported dsl_version')

    try:
        check_config(request.json, required_keys + config_keys)
    except Exception as e:
        return error_response(400, str(e))

    try:
        parser_class.validate_component_param(
            get_federatedml_setting_conf_directory(),
            {i: request.json[i] for i in config_keys},
            *[request.json[i] for i in required_keys])
    except Exception as e:
        return error_response(400, str(e))

    return get_json_result()
