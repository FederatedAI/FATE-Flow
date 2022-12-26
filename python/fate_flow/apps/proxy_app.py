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
from flask.json import jsonify

from fate_arch.common import FederatedMode

from fate_flow.utils.api_utils import federated_api, forward_api, proxy_api


page_name = 'forward'


@manager.route('/<role>', methods=['POST'])
def start_proxy(role):
    _job_id = f'{role}_forward'
    request_config = request.json or request.form.to_dict()

    if request_config.get('header') and request_config.get('body'):
        request_config['header'] = {
            **request.headers,
            **{
                k.replace('_', '-').upper(): v
                for k, v in request_config['header'].items()
            },
        }
    else:
        request_config = {
            'header': request.headers,
            'body': request_config,
        }

    response = (
        proxy_api(role, _job_id, request_config) if role == 'marketplace'
        else federated_api(
            _job_id, 'POST', f'/forward/{role}/do',
            request_config['header'].get('SRC-PARTY-ID'),
            request_config['header'].get('DEST-PARTY-ID'),
            '', request_config, FederatedMode.MULTIPLE,
        )
    )
    return jsonify(response)


@manager.route('/<role>/do', methods=['POST'])
def start_forward(role):
    request_config = request.json or request.form.to_dict()
    return jsonify(forward_api(role, request_config))
