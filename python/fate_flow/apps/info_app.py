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
import socket

from flask import request
from flask.json import jsonify

from fate_arch.common import FederatedMode

from fate_flow.db.runtime_config import RuntimeConfig
from fate_flow.db.service_registry import ServerRegistry
from fate_flow.settings import API_VERSION, GRPC_PORT, HOST, HTTP_PORT, PARTY_ID
from fate_flow.utils.api_utils import error_response, federated_api, get_json_result


@manager.route('/common', methods=['POST'])
def get_common_info():
    return get_json_result(data={
        'version': RuntimeConfig.get_env('FATE'),
        'host': HOST,
        'http_port': HTTP_PORT,
        'grpc_port': GRPC_PORT,
        'party_id': PARTY_ID,
    })


@manager.route('/fateboard', methods=['POST'])
def get_fateboard_info():
    host = ServerRegistry.FATEBOARD.get('host')
    port = ServerRegistry.FATEBOARD.get('port')
    if not host or not port:
        return error_response(404, 'fateboard is not configured')

    return get_json_result(data={
        'host': host,
        'port': port,
    })


# TODO: send greetings message using grpc protocol
@manager.route('/eggroll', methods=['POST'])
def get_eggroll_info():
    conf = ServerRegistry.FATE_ON_EGGROLL['rollsite']
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        r = s.connect_ex((conf['host'], conf['port']))
        if r != 0:
            return error_response(503)

    return error_response(200)


@manager.route('/version', methods=['POST'])
@app.route(f'/{API_VERSION}/version/get', methods=['POST'])
def get_version():
    module = request.json['module'] if isinstance(request.json, dict) and request.json.get('module') else 'FATE'
    version = RuntimeConfig.get_env(module)
    if version is None:
        return error_response(404, f'unknown module {module}')

    return get_json_result(data={
        module: version,
        'API': API_VERSION,
    })


@manager.route('/party/<dest_party_id>', methods=['POST'])
def get_party_info(dest_party_id):
    response = federated_api(
        'party_info', 'POST', '/info/common',
        PARTY_ID, dest_party_id, '',
        {}, FederatedMode.MULTIPLE,
    )
    return jsonify(response)


@manager.route('/party/<proxy_party_id>/<dest_party_id>', methods=['POST'])
def get_party_info_from_another_party(proxy_party_id, dest_party_id):
    response = federated_api(
        'party_info', 'POST', f'/info/party/{dest_party_id}',
        PARTY_ID, proxy_party_id, '',
        {}, FederatedMode.MULTIPLE,
    )
    return jsonify(response)
