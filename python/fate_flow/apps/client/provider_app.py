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
from fate_flow.manager.service.provider_manager import ProviderManager
from fate_flow.utils.api_utils import API


@manager.route('/register', methods=['POST'])
@API.Input.json(name=fields.String(required=True))
@API.Input.json(device=fields.String(required=True))
@API.Input.json(version=fields.String(required=True))
@API.Input.json(metadata=fields.Dict(required=True))
def register(name, device, version, metadata):
    provider = ProviderManager.get_provider(name=name, device=device, version=version, metadata=metadata)
    if provider:
        operator_type = ProviderManager.register_provider(provider)
        return API.Output.json(message=f"{operator_type} success")
    else:
        return API.Output.json(code=ReturnCode.Provider.DEVICE_NOT_SUPPORTED, message=device)


@manager.route('/query', methods=['GET'])
@API.Input.params(name=fields.String(required=False))
@API.Input.params(device=fields.String(required=False))
@API.Input.params(version=fields.String(required=False))
@API.Input.params(provider_name=fields.String(required=False))
def query(name=None, device=None, version=None, provider_name=None):
    providers = ProviderManager.query_provider(name=name, device=device, version=version, provider_name=provider_name)
    return API.Output.json(data=[provider.to_human_model_dict() for provider in providers])


@manager.route('/delete', methods=['POST'])
@API.Input.json(name=fields.String(required=False))
@API.Input.json(device=fields.String(required=False))
@API.Input.json(version=fields.String(required=False))
@API.Input.json(provider_name=fields.String(required=False))
def delete(name=None, device=None, version=None, provider_name=None):
    result = ProviderManager.delete_provider(name=name, device=device, version=version, provider_name=provider_name)
    return API.Output.json(data=result)
