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
import random
import time
from functools import wraps

import marshmallow
from flask import jsonify, send_file, request as flask_request

from webargs.flaskparser import parser

from fate_flow.entity.types import CoordinationProxyService, CoordinationCommunicationProtocol, FederatedMode
from fate_flow.entity.code import ReturnCode
from fate_flow.errors import FateFlowError
from fate_flow.hook import HookManager
from fate_flow.hook.common.parameters import SignatureParameters
from fate_flow.runtime.job_default_config import JobDefaultConfig
from fate_flow.runtime.system_settings import PROXY_NAME, ENGINES, PROXY, HOST, HTTP_PORT, API_VERSION, \
    REQUEST_TRY_TIMES, REQUEST_MAX_WAIT_SEC, REQUEST_WAIT_SEC
from fate_flow.utils.log import getLogger
from fate_flow.utils.log_utils import schedule_logger, audit_logger
from fate_flow.utils.requests_utils import request

parser.unknown = marshmallow.EXCLUDE

stat_logger = getLogger()


class API:
    class Input:
        @staticmethod
        def params(**kwargs):
            return parser.use_kwargs(kwargs, location='querystring')

        @staticmethod
        def form(**kwargs):
            return parser.use_kwargs(kwargs, location='form')

        @staticmethod
        def files(**kwargs):
            return parser.use_kwargs(kwargs, location='files')

        @staticmethod
        def json(**kwargs):
            return parser.use_kwargs(kwargs, location='json')

        @staticmethod
        def headers(**kwargs):
            return parser.use_kwargs(kwargs, location="headers")

    class Output:
        @staticmethod
        def json(code=ReturnCode.Base.SUCCESS, message='success', data=None, job_id=None, **kwargs):
            result_dict = {
                "code": code,
                "message": message,
                "data": data,
                "job_id": job_id,
            }

            response = {}
            for key, value in result_dict.items():
                if value is not None:
                    response[key] = value
            # extra resp
            for key, value in kwargs.items():
                response[key] = value
            return jsonify(response)

        @staticmethod
        def file(path_or_file, attachment_filename, as_attachment, mimetype="application/octet-stream"):
            return send_file(path_or_file, download_name=attachment_filename, as_attachment=as_attachment, mimetype=mimetype)

        @staticmethod
        def server_error_response(e):
            if isinstance(e, FateFlowError):
                return API.Output.json(code=e.code, message=e.message)
            stat_logger.exception(e)
            if len(e.args) > 1:
                if isinstance(e.args[0], int):
                    return API.Output.json(code=e.args[0], message=e.args[1])
                else:
                    return API.Output.json(code=ReturnCode.Server.EXCEPTION, message=repr(e))
            return API.Output.json(code=ReturnCode.Server.EXCEPTION, message=repr(e))

        @staticmethod
        def args_error_response(e):
            stat_logger.exception(e)
            messages = e.data.get("messages", {})
            return API.Output.json(code=ReturnCode.API.INVALID_PARAMETER, message="Invalid request.", data=messages)

        @staticmethod
        def fate_flow_exception(e: FateFlowError):
            return API.Output.json(code=e.code, message=e.message)

        @staticmethod
        def runtime_exception(code):
            def _outer(func):
                @wraps(func)
                def _wrapper(*args, **kwargs):
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        if isinstance(e, FateFlowError):
                            raise e
                        else:
                            message = f"Request uri {flask_request.base_url} failed: {str(e)}"
                            return API.Output.json(code=code, message=message)
                return _wrapper
            return _outer


def get_federated_proxy_address():
    # protocol = CoordinationCommunicationProtocol.HTTP
    proxy_name = PROXY_NAME
    if ENGINES.get("federated_mode") == FederatedMode.SINGLE:
        return HOST, HTTP_PORT, CoordinationCommunicationProtocol.HTTP, PROXY_NAME
    if proxy_name == CoordinationProxyService.OSX:
        host = PROXY.get(proxy_name).get("host")
        port = PROXY.get(proxy_name).get("port")
        proxy_name = CoordinationProxyService.ROLLSITE
        protocol = CoordinationCommunicationProtocol.GRPC

    elif proxy_name == CoordinationProxyService.ROLLSITE:
        host = PROXY.get(proxy_name).get("host")
        port = PROXY.get(proxy_name).get("port")
        protocol = CoordinationCommunicationProtocol.GRPC

    elif proxy_name == CoordinationProxyService.NGINX:
        protocol = PROXY.get(proxy_name).get("protocol", "http")
        host = PROXY.get(proxy_name).get(f"host")
        port = PROXY.get(proxy_name).get(f"{protocol}_port")
    else:
        raise RuntimeError(f"Can not support coordinate proxy {proxy_name}， all proxy {PROXY.keys()}")
    return host, port, protocol, proxy_name


def generate_headers(party_id, body, initiator_party_id=""):
    return HookManager.site_signature(
        SignatureParameters(party_id=party_id, body=body, initiator_party_id=initiator_party_id))


def get_exponential_backoff_interval(retries, full_jitter=False):
    """Calculate the exponential backoff wait time."""
    # Will be zero if factor equals 0
    countdown = min(REQUEST_MAX_WAIT_SEC, REQUEST_WAIT_SEC * (2 ** retries))
    # Full jitter according to
    # https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/
    if full_jitter:
        countdown = random.randrange(countdown + 1)
    # Adjust according to maximum wait time and account for negative values.
    return max(0, countdown)


def federated_coordination_on_http(method, host, port, endpoint, json_body, headers=None, params=None,
                                   timeout=JobDefaultConfig.remote_request_timeout):
    url = f'http://{host}:{port}/{API_VERSION}{endpoint}'
    for t in range(REQUEST_TRY_TIMES):
        try:
            response = request(
                method=method, url=url, timeout=timeout,
                headers=headers, json=json_body, params=params
            )
            response.raise_for_status()
        except Exception as e:
            schedule_logger().warning(f'http api error: {url}\n{e}')
            if t >= REQUEST_TRY_TIMES - 1:
                raise e
        else:
            audit_logger().info(f'http api response: {url}\n{response.text}')
            return response.json()
        time.sleep(get_exponential_backoff_interval(t))
