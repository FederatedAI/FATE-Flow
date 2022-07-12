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

from fate_flow.db.key_manager import RsaKeyManager
from fate_flow.entity.types import SiteKeyName
from fate_flow.utils.api_utils import get_json_result


@manager.route('/public/save', methods=['POST'])
def save_public_key():
    request_conf = request.json
    result = RsaKeyManager.create_or_update(request_conf.get("party_id"), request_conf.get("key"))
    return get_json_result(data=result)


@manager.route('/query', methods=['POST'])
def query_public_key():
    request_conf = request.json
    data = RsaKeyManager.get_key(request_conf.get("party_id"), key_name=request_conf.get("key_name", SiteKeyName.PUBLIC.value))
    return get_json_result(data=data)


@manager.route('/public/delete', methods=['POST'])
def delete_public_key():
    request_conf = request.json
    RsaKeyManager.delete(request_conf.get("party_id"))
    return get_json_result()