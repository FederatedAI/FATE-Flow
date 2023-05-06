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
from fate_flow.manager.service.service_manager import ServiceRegistry, ServerRegistry
from fate_flow.runtime.runtime_config import RuntimeConfig
from fate_flow.utils.api_utils import API


@manager.route('/fateflow', methods=['GET'])
def fate_flow_server_info():
    data = RuntimeConfig.SERVICE_DB.get_servers()
    return API.Output.json(data=data)


@manager.route('/query/all', methods=['GET'])
def query_all():
    data = ServerRegistry.get_all()
    return API.Output.json(data=data)


@manager.route('/query', methods=['GET'])
@API.Input.params(server_name=fields.String(required=True))
def query_server(server_name):
    server_list = ServerRegistry.query_server_info_from_db(server_name)
    if not server_list:
        return API.Output.json(code=ReturnCode.Server.NO_FOUND, message=f"no found server {server_name}")
    return API.Output.json(data=server_list[0].to_human_model_dict())


@manager.route('/registry', methods=['POST'])
@API.Input.json(server_name=fields.String(required=True))
@API.Input.json(host=fields.String(required=True))
@API.Input.json(port=fields.Integer(required=True))
@API.Input.json(protocol=fields.String(required=False))
def register_server(server_name, host, port, protocol="http"):
    server_info = ServerRegistry.register(server_name, host, port, protocol)
    return API.Output.json(data=server_info)


@manager.route('/delete', methods=['POST'])
@API.Input.json(server_name=fields.String(required=True))
def delete_server(server_name):
    status = ServerRegistry.delete_server_from_db(server_name)
    return API.Output.json(message="success" if status else "failed")


@manager.route('/service/query', methods=['GET'])
@API.Input.params(server_name=fields.String(required=True))
@API.Input.params(service_name=fields.String(required=True))
def query_service(server_name, service_name):
    service_list = ServiceRegistry.load_service(server_name=server_name, service_name=service_name)
    if not service_list:
        return API.Output.json(code=ReturnCode.Server.NO_FOUND, message=f"no found server {server_name}")
    return API.Output.json(data=service_list[0].to_human_model_dict())


@manager.route('/service/registry', methods=['POST'])
@API.Input.json(server_name=fields.String(required=True))
@API.Input.json(service_name=fields.String(required=True))
@API.Input.json(uri=fields.String(required=True))
@API.Input.json(method=fields.String(required=False))
@API.Input.json(params=fields.Dict(required=False))
@API.Input.json(data=fields.Dict(required=False))
@API.Input.json(headers=fields.Dict(required=False))
@API.Input.json(protocol=fields.String(required=False))
def registry_service(server_name, service_name, uri, method="POST", params=None, data=None, headers=None, protocol="http"):
    ServiceRegistry.save_service_info(server_name=server_name, service_name=service_name, uri=uri, method=method,
                                      params=params, data=data, headers=headers, protocol=protocol)
    return API.Output.json()


@manager.route('/service/delete', methods=['POST'])
@API.Input.json(server_name=fields.String(required=True))
@API.Input.json(service_name=fields.String(required=True))
def delete_service(server_name, service_name):
    status = ServiceRegistry.delete(server_name, service_name)
    return API.Output.json(message="success" if status else "failed")
