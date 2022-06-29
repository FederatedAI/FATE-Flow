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
import functools
import json
import time
from functools import wraps
import flask

from flask import Response, jsonify, request as flask_request
from werkzeug.http import HTTP_STATUS_CODES

from fate_arch.common import CoordinationCommunicationProtocol, CoordinationProxyService, FederatedMode
from fate_arch.common.base_utils import json_loads
from fate_flow.db.job_default_config import JobDefaultConfig
from fate_flow.db.runtime_config import RuntimeConfig
from fate_flow.db.service_registry import ServerRegistry
from fate_flow.entity import RetCode
from fate_flow.hook.common.parameters import SignatureParameters
from fate_flow.settings import API_VERSION, HEADERS, PROXY, PROXY_PROTOCOL, stat_logger, PERMISSION_SWITCH, \
    SITE_AUTHENTICATION, HOST, HTTP_PORT, PARTY_ID, REQUEST_TRY_TIMES
from fate_flow.utils.base_utils import compare_version
from fate_flow.utils.grpc_utils import forward_grpc_packet, gen_routing_metadata, get_command_federation_channel, \
    wrap_grpc_packet
from fate_flow.hook import HookManager
from fate_flow.utils.log_utils import audit_logger, schedule_logger
from fate_flow.utils.permission_utils import get_permission_parameters
from fate_flow.utils.requests_utils import request


def get_json_result(retcode=RetCode.SUCCESS, retmsg='success', data=None, job_id=None, meta=None):
    result_dict = {"retcode": retcode, "retmsg": retmsg, "data": data, "jobId": job_id, "meta": meta}
    response = {}
    for key, value in result_dict.items():
        if value is None and key != "retcode":
            continue
        else:
            response[key] = value
    return jsonify(response)


def server_error_response(e):
    stat_logger.exception(e)
    if len(e.args) > 1:
        return get_json_result(retcode=RetCode.EXCEPTION_ERROR, retmsg=str(e.args[0]), data=e.args[1])
    else:
        return get_json_result(retcode=RetCode.EXCEPTION_ERROR, retmsg=str(e))


def error_response(response_code, retmsg=None):
    if retmsg is None:
        retmsg = HTTP_STATUS_CODES.get(response_code, 'Unknown Error')
    return Response(json.dumps({'retmsg': retmsg, 'retcode': response_code}), status=response_code, mimetype='application/json')


def federated_api(job_id, method, endpoint, src_party_id, dest_party_id, src_role, json_body, federated_mode, api_version=API_VERSION,
                  overall_timeout=None):
    overall_timeout = JobDefaultConfig.remote_request_timeout if overall_timeout is None else overall_timeout
    headers = generate_headers(src_party_id, src_role, json_body)
    if int(dest_party_id) == 0:
        federated_mode = FederatedMode.SINGLE
    if federated_mode == FederatedMode.SINGLE:
        return local_api(job_id=job_id, method=method, endpoint=endpoint, json_body=json_body, api_version=api_version, headers=headers)
    elif federated_mode == FederatedMode.MULTIPLE:
        host, port, protocol = get_federated_proxy_address(src_party_id, dest_party_id)
        if protocol == CoordinationCommunicationProtocol.HTTP:
            return federated_coordination_on_http(job_id=job_id, method=method, host=host,
                                                  port=port, endpoint=endpoint, src_party_id=src_party_id, src_role=src_role,
                                                  dest_party_id=dest_party_id, json_body=json_body, api_version=api_version, overall_timeout=overall_timeout,
                                                  headers=headers)
        elif protocol == CoordinationCommunicationProtocol.GRPC:
            return federated_coordination_on_grpc(job_id=job_id, method=method, host=host,
                                                  port=port, endpoint=endpoint, src_party_id=src_party_id, src_role=src_role,
                                                  dest_party_id=dest_party_id, json_body=json_body, api_version=api_version,
                                                  overall_timeout=overall_timeout, headers=headers)
        else:
            raise Exception(f"{protocol} coordination communication protocol is not supported.")
    else:
        raise Exception('{} work mode is not supported'.format(federated_mode))


def local_api(job_id, method, endpoint, json_body, api_version=API_VERSION, try_times=3, headers=None):
    return federated_coordination_on_http(job_id=job_id, method=method, host=RuntimeConfig.JOB_SERVER_HOST,
                                          port=RuntimeConfig.HTTP_PORT, endpoint=endpoint, src_party_id=PARTY_ID, src_role="",
                                          dest_party_id=PARTY_ID, json_body=json_body, api_version=api_version,
                                          try_times=try_times, headers=headers)


def get_federated_proxy_address(src_party_id, dest_party_id):
    if isinstance(PROXY, str):
        if PROXY == CoordinationProxyService.ROLLSITE:
            proxy_address = ServerRegistry.FATE_ON_EGGROLL.get(PROXY)
            return proxy_address["host"], proxy_address.get("grpc_port", proxy_address["port"]), CoordinationCommunicationProtocol.GRPC
        elif PROXY == CoordinationProxyService.NGINX:
            proxy_address = ServerRegistry.FATE_ON_SPARK.get(PROXY)
            protocol = CoordinationCommunicationProtocol.HTTP if PROXY_PROTOCOL == "default" else PROXY_PROTOCOL
            return proxy_address["host"], proxy_address[f"{protocol}_port"], protocol
        else:
            raise RuntimeError(f"can not support coordinate proxy {PROXY}")
    elif isinstance(PROXY, dict):
        proxy_address = PROXY
        protocol = CoordinationCommunicationProtocol.HTTP if PROXY_PROTOCOL == "default" else PROXY_PROTOCOL
        proxy_name = PROXY.get("name", CoordinationProxyService.FATEFLOW)
        if proxy_name == CoordinationProxyService.FATEFLOW and str(dest_party_id) == str(src_party_id):
            host = RuntimeConfig.JOB_SERVER_HOST
            port = RuntimeConfig.HTTP_PORT
        else:
            host = proxy_address["host"]
            port = proxy_address[f"{protocol}_port"]
        return host, port, protocol
    else:
        raise RuntimeError(f"can not support coordinate proxy config {PROXY}")


def federated_coordination_on_http(job_id, method, host, port, endpoint, src_party_id, src_role, dest_party_id, json_body, api_version=API_VERSION, overall_timeout=None, try_times=REQUEST_TRY_TIMES, headers=None):
    try_times = max(try_times, 1)

    if not headers:
        headers = generate_headers(src_party_id, src_role, json_body)
    overall_timeout = JobDefaultConfig.remote_request_timeout if overall_timeout is None else overall_timeout
    endpoint = f"/{api_version}{endpoint}"

    url = "http://{}:{}{}".format(host, port, endpoint)
    audit_logger(job_id).info(f'remote http api request: {url}')
    headers.update(HEADERS)
    headers["dest-party-id"] = str(dest_party_id)

    for t in range(try_times):
        try:
            response = request(method=method, url=url, json=json_body, headers=headers)
        except Exception as e:
            if t == try_times - 1:
                raise e

            schedule_logger(job_id).warning(f'remote http request {endpoint} error, sleep and try again')
            time.sleep(2 * (t + 1))
            continue
        else:
            audit_logger(job_id).info(f'remote http api response: {endpoint} {response.text}')
            return response.json()


def federated_coordination_on_grpc(job_id, method, host, port, endpoint, src_party_id, src_role, dest_party_id, json_body, api_version=API_VERSION,
                                   overall_timeout=None, try_times=REQUEST_TRY_TIMES, headers=None):
    overall_timeout = JobDefaultConfig.remote_request_timeout if overall_timeout is None else overall_timeout
    endpoint = f"/{api_version}{endpoint}"
    _packet = wrap_grpc_packet(json_body, method, endpoint, src_party_id, dest_party_id, job_id,
                               overall_timeout=overall_timeout, headers=headers)
    _routing_metadata = gen_routing_metadata(src_party_id=src_party_id, dest_party_id=dest_party_id)
    exception = None
    for t in range(try_times):
        try:
            channel, stub = get_command_federation_channel(host, port)
            _return, _call = stub.unaryCall.with_call(_packet, metadata=_routing_metadata, timeout=(overall_timeout/1000))
            audit_logger(job_id).info("grpc api response: {}".format(_return))
            channel.close()
            response = json_loads(_return.body.value)
            return response
        except Exception as e:
            exception = e
            schedule_logger(job_id).warning(f"remote request {endpoint} error, sleep and try again")
            time.sleep(2 * (t+1))
    else:
        tips = 'Please check rollSite and fateflow network connectivity'
        """
        if 'Error received from peer' in str(exception):
            tips = 'Please check if the fate flow server of the other party is started. '
        if 'failed to connect to all addresses' in str(exception):
            tips = 'Please check whether the rollsite service(port: 9370) is started. '
        """
        raise Exception('{}rpc request error: {}'.format(tips, exception))


def proxy_api(role, _job_id, request_config):
    job_id = request_config.get('header').get('job_id', _job_id)
    method = request_config.get('header').get('method', 'POST')
    endpoint = request_config.get('header').get('endpoint')
    src_party_id = request_config.get('header').get('src_party_id')
    dest_party_id = request_config.get('header').get('dest_party_id')
    json_body = request_config.get('body')
    _packet = forward_grpc_packet(json_body, method, endpoint, src_party_id, dest_party_id, job_id=job_id, role=role)
    _routing_metadata = gen_routing_metadata(src_party_id=src_party_id, dest_party_id=dest_party_id)
    host, port, protocol = get_federated_proxy_address(src_party_id, dest_party_id)
    channel, stub = get_command_federation_channel(host, port)
    _return, _call = stub.unaryCall.with_call(_packet, metadata=_routing_metadata)
    channel.close()
    json_body = json_loads(_return.body.value)
    return json_body


def forward_api(role, request_config):
    method = request_config.get('header', {}).get('method', 'post')
    endpoint = request_config.get('header', {}).get('endpoint')
    ip = getattr(ServerRegistry, role.upper()).get("host")
    port = getattr(ServerRegistry, role.upper()).get("port")
    url = "http://{}:{}{}".format(ip, port, endpoint)
    audit_logger().info('api request: {}'.format(url))

    http_response = request(method=method, url=url, json=request_config.get('body'), headers=request_config.get('header'))
    if http_response.status_code == 200:
        response = http_response.json()
    else:
        response =  {"retcode": http_response.status_code, "retmsg": http_response.text}
    audit_logger().info(response)
    return response


def generate_headers(src_party_id, src_role, body):
    headers = common_headers()
    headers.update(src_parm(role=src_role, party_id=src_party_id))
    sign_dict = sign_parm(src_party_id, body)
    if sign_dict is not None:
        headers.update(sign_dict)
    return headers


def common_headers():
    return {"src_fate_ver": RuntimeConfig.get_env('FATE')}


def src_parm(role, party_id):
    return {"src_role": role, "src_party_id": str(party_id)}


def sign_parm(dest_party_id, body):
    # generate signature
    if SITE_AUTHENTICATION:
        sign_obj = HookManager.site_signature(SignatureParameters(PARTY_ID, body))
        return {"signature": sign_obj.signature}


def create_job_request_check(func):
    @functools.wraps(func)
    def _wrapper(*_args, **_kwargs):
        party_id = _kwargs.get("party_id")
        role = _kwargs.get("role")
        body = flask_request.json
        headers = flask_request.headers

        # permission check
        if PERMISSION_SWITCH:
            permission_return = HookManager.permission_check(get_permission_parameters(role, party_id, body))
            if permission_return.code != RetCode.SUCCESS:
                return get_json_result(
                    retcode=RetCode.PERMISSION_ERROR,
                    retmsg='permission check failed',
                    data=permission_return.to_dict()
                )

        # version check
        src_fate_ver = headers.get('src_fate_ver')
        if src_fate_ver is not None and compare_version(src_fate_ver, '1.7.0') == 'lt':
            return get_json_result(retcode=RetCode.INCOMPATIBLE_FATE_VER, retmsg='Incompatible FATE versions',
                                   data={'src_fate_ver': src_fate_ver,
                                         "current_fate_ver": RuntimeConfig.get_env('FATE')})
        return func(*_args, **_kwargs)
    return _wrapper


def validate_request(*args, **kwargs):
    def wrapper(func):
        @wraps(func)
        def decorated_function(*_args, **_kwargs):
            input_arguments = flask.request.json or flask.request.form.to_dict()
            no_arguments = []
            error_arguments = []
            for arg in args:
                if arg not in input_arguments:
                    no_arguments.append(arg)
            for k, v in kwargs.items():
                config_value = input_arguments.get(k, None)
                if config_value is None:
                    no_arguments.append(k)
                elif isinstance(v, (tuple, list)):
                    if config_value not in v:
                        error_arguments.append((k, set(v)))
                elif config_value != v:
                    error_arguments.append((k, v))
            if no_arguments or error_arguments:
                error_string = ""
                if no_arguments:
                    error_string += "required argument are missing: {}; ".format(",".join(no_arguments))
                if error_arguments:
                    error_string += "required argument values: {}".format(",".join(["{}={}".format(a[0], a[1]) for a in error_arguments]))
                return get_json_result(retcode=RetCode.ARGUMENT_ERROR, retmsg=error_string)
            return func(*_args, **_kwargs)
        return decorated_function
    return wrapper


def cluster_route(func):
    @functools.wraps(func)
    def _route(*args, **kwargs):
        instance_id = flask_request.json.get("instance_id")
        if instance_id:
            instance_list = RuntimeConfig.SERVICE_DB.get_servers()
            for instance in instance_list:
                if instance.get("instance_id") == instance_id:
                    dest_address = instance.get("http_address")
                    if f"{HOST}:{HTTP_PORT}" == dest_address:
                        break
                    dest_url = flask_request.url.replace(f"{HOST}:{HTTP_PORT}", dest_address)

                    response = request(method=flask_request.method, url=dest_url, json=flask_request.json,
                                       headers=flask_request.headers)
                    if response.status_code == 200:
                        response = response.json()
                        return get_json_result(**response)
                    else:
                        return get_json_result(retcode=response.status_code, retmsg=response.text)
        return func(*args, **kwargs)
    return _route

