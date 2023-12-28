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

from fate_flow.apps.desc import PROVIDER_NAME, DEVICE, VERSION, COMPONENT_METADATA, PROVIDER_ALL_NAME, \
    COMPONENTS_DESCRIPTION, PROTOCOL
from fate_flow.errors.server_error import DeviceNotSupported
from fate_flow.manager.service.provider_manager import ProviderManager
from fate_flow.utils.api_utils import API


@manager.route('/register', methods=['POST'])
@API.Input.json(name=fields.String(required=True), desc=PROVIDER_NAME)
@API.Input.json(device=fields.String(required=True), desc=DEVICE)
@API.Input.json(version=fields.String(required=True), desc=VERSION)
@API.Input.json(metadata=fields.Dict(required=True), desc=COMPONENT_METADATA)
@API.Input.json(protocol=fields.String(required=False), desc=PROTOCOL)
@API.Input.json(components_description=fields.Dict(required=False), desc=COMPONENTS_DESCRIPTION)
def register(name, device, version, metadata, components_description=None, protocol=None):
    provider = ProviderManager.get_provider(name=name, device=device, version=version, metadata=metadata, check=True)
    if provider:
        operator_type = ProviderManager.register_provider(provider, components_description, protocol)
        return API.Output.json(message=f"{operator_type} success")
    else:
        return API.Output.fate_flow_exception(DeviceNotSupported(device=device))


@manager.route('/query', methods=['GET'])
@API.Input.params(name=fields.String(required=False), desc=PROVIDER_NAME)
@API.Input.params(device=fields.String(required=False), desc=DEVICE)
@API.Input.params(version=fields.String(required=False), desc=VERSION)
@API.Input.params(provider_name=fields.String(required=False), desc=PROVIDER_ALL_NAME)
def query(name=None, device=None, version=None, provider_name=None):
    providers = ProviderManager.query_provider(name=name, device=device, version=version, provider_name=provider_name)
    return API.Output.json(data=[provider.to_human_model_dict() for provider in providers])


@manager.route('/delete', methods=['POST'])
@API.Input.json(name=fields.String(required=False), desc=PROVIDER_NAME)
@API.Input.json(device=fields.String(required=False), desc=DEVICE)
@API.Input.json(version=fields.String(required=False), desc=VERSION)
@API.Input.json(provider_name=fields.String(required=False), desc=PROVIDER_ALL_NAME)
def delete(name=None, device=None, version=None, provider_name=None):
    result = ProviderManager.delete_provider(name=name, device=device, version=version, provider_name=provider_name)
    return API.Output.json(data=result)
