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

from fate_flow.db.service_registry import ServiceRegistry, ServerRegistry
from fate_flow.utils.api_utils import get_json_result, validate_request


@manager.route("/registry", methods=['POST'])
def create_service():
    service_info = request.json
    # compatibility
    update_server = {}
    if "server_name" not in service_info:
        update_server = ServerRegistry.save(request.json)
    else:
        ServiceRegistry.save_service_info(**request.json)
    return get_json_result(data=update_server)


@manager.route('/query', methods=['POST'])
@validate_request("service_name")
def get_service():
    service_info = ServiceRegistry.load_service(**request.json)
    return get_json_result(data={"service_info": [service.to_json() for service in service_info]})