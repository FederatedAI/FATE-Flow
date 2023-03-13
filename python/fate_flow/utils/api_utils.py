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
import marshmallow
from flask import jsonify

from webargs.flaskparser import parser

from fate_flow.entity.types import CoordinationProxyService, CoordinationCommunicationProtocol, FederatedMode
from fate_flow.entity.code import ReturnCode
from fate_flow.hook import HookManager
from fate_flow.hook.common.parameters import SignatureParameters
from fate_flow.runtime.system_settings import stat_logger, PROXY_NAME, ENGINES, PROXY, HOST, HTTP_PORT

parser.unknown = marshmallow.EXCLUDE


class API:
    class Input:
        @staticmethod
        def params(**kwargs):
            return parser.use_kwargs(kwargs, location='querystring')

        @staticmethod
        def json(**kwargs):
            return parser.use_kwargs(kwargs, location='json')

        @staticmethod
        def headers(**kwargs):
            return parser.use_kwargs(kwargs, location="headers")

    class Output:
        @staticmethod
        def json(code=ReturnCode.Base.SUCCESS, message='success', data=None, job_id=None, meta=None):
            result_dict = {
                "code": code,
                "message": message,
                "data": data,
                "job_id": job_id,
                "meta": meta,
            }

            response = {}
            for key, value in result_dict.items():
                if value is not None:
                    response[key] = value
            return jsonify(response)

        @staticmethod
        def server_error_response(e):
            stat_logger.exception(e)
            if len(e.args) > 1:
                return API.Output.json(code=e.args[0], message=e.args[1])
            return API.Output.json(code=ReturnCode.Server.EXCEPTION, message=repr(e))

        @staticmethod
        def args_error_response(e):
            stat_logger.exception(e)
            messages = e.data.get("messages", {})
            return API.Output.json(code=ReturnCode.API.INVALID_PARAMETER, message="Invalid request.", data=messages)


def get_federated_proxy_address():
    # protocol = CoordinationCommunicationProtocol.HTTP
    if ENGINES.get("federated_mode") == FederatedMode.SINGLE:
        return HOST, HTTP_PORT, CoordinationCommunicationProtocol.HTTP, PROXY_NAME
    if PROXY_NAME == CoordinationProxyService.OSX:
        host = PROXY.get(PROXY_NAME).get("host")
        port = PROXY.get(PROXY_NAME).get("port")
        protocol = CoordinationCommunicationProtocol.GRPC

    elif PROXY_NAME == CoordinationProxyService.ROLLSITE:
        host = PROXY.get(PROXY_NAME).get("host")
        port = PROXY.get(PROXY_NAME).get("port")
        protocol = CoordinationCommunicationProtocol.GRPC

    elif PROXY_NAME == CoordinationProxyService.NGINX:
        protocol = PROXY.get(PROXY_NAME).get("protocol", "http")
        host = PROXY.get(PROXY_NAME).get(f"host")
        port = PROXY.get(PROXY_NAME).get(f"{protocol}_port")
    else:
        raise RuntimeError(f"can not support coordinate proxy {PROXY_NAME}， all proxy {PROXY.keys()}")
    return host, port, protocol, PROXY_NAME


def generate_headers(party_id, body):
    return HookManager.site_signature(SignatureParameters(party_id=party_id, body=body))