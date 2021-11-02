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

from fate_flow.db.service_registry import ServiceRegistry
from fate_flow.utils.api_utils import get_json_result


@manager.route('/registry', methods=['POST'])
def register_service():
    update_server = ServiceRegistry.save(request.json)
    return get_json_result(data={"update_server": update_server})


@manager.route('/query', methods=['POST'])
def get_service():
    service_info = ServiceRegistry.query(request.json.get("service_name"))
    return get_json_result(data={"service_info": service_info})