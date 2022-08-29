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
import json
import random
import time
from functools import wraps
from io import BytesIO

from flask import (
    Response, jsonify, send_file,
    request as flask_request,
)
from werkzeug.http import HTTP_STATUS_CODES

from fate_arch.common import (
    CoordinationCommunicationProtocol, CoordinationProxyService,
    FederatedMode,
)
from fate_arch.common.base_utils import json_dumps, json_loads
from fate_arch.common.versions import get_fate_version

from fate_flow.db.job_default_config import JobDefaultConfig
from fate_flow.db.runtime_config import RuntimeConfig
from fate_flow.db.service_registry import ServerRegistry
from fate_flow.entity import RetCode
from fate_flow.hook import HookManager
from fate_flow.hook.common.parameters import SignatureParameters
from fate_flow.settings import (
    API_VERSION, FATE_FLOW_SERVICE_NAME, HOST, HTTP_PORT,
    PARTY_ID, PERMISSION_SWITCH, PROXY, PROXY_PROTOCOL,
    REQUEST_MAX_WAIT_SEC, REQUEST_TRY_TIMES, REQUEST_WAIT_SEC,
    SITE_AUTHENTICATION, stat_logger,
)
from fate_flow.utils.base_utils import compare_version
from fate_flow.utils.grpc_utils import (
    forward_grpc_packet, gen_routing_metadata,
    get_command_federation_channel, wrap_grpc_packet,
)
from fate_flow.utils.log_utils import audit_logger, schedule_logger
from fate_flow.utils.permission_utils import get_permission_parameters
from fate_flow.utils.requests_utils import request


fate_version = get_fate_version() or ''
request_headers = {
    'User-Agent': f'{FATE_FLOW_SERVICE_NAME}/{fate_version}',
    'service': FATE_FLOW_SERVICE_NAME,
    'src_fate_ver': fate_version,
}


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


def get_json_result(retcode=RetCode.SUCCESS, retmsg='success', data=None, job_id=None, meta=None):
    result_dict = {
        "retcode": retcode,
        "retmsg": retmsg,
        "data": data,
        "jobId": job_id,
        "meta": meta,
    }

    response = {}
    for key, value in result_dict.items():
        if value is not None:
            response[key] = value
    return jsonify(response)


def server_error_response(e):
    stat_logger.exception(e)

    if len(e.args) > 1:
        return get_json_result(retcode=RetCode.EXCEPTION_ERROR, retmsg=repr(e.args[0]), data=e.args[1])
    return get_json_result(retcode=RetCode.EXCEPTION_ERROR, retmsg=repr(e))


def error_response(response_code, retmsg=None):
    if retmsg is None:
        retmsg = HTTP_STATUS_CODES.get(response_code, 'Unknown Error')

    return Response(json.dumps({
        'retmsg': retmsg,
        'retcode': response_code,
    }), status=response_code, mimetype='application/json')


def federated_api(job_id, method, endpoint, src_party_id, dest_party_id, src_role, json_body, federated_mode):
    src_party_id = str(src_party_id or '')
    dest_party_id = str(dest_party_id or '')
    src_role = src_role or ''

    headers = request_headers.copy()
    headers.update({
        'src_party_id': src_party_id,
        'dest_party_id': dest_party_id,
        'src_role': src_role,
    })

    if SITE_AUTHENTICATION:
        sign_obj = HookManager.site_signature(SignatureParameters(PARTY_ID, json_body))
        headers['site_signature'] = sign_obj.site_signature or ''

    kwargs = {
        'job_id': job_id,
        'method': method,
        'endpoint': endpoint,
        'src_party_id': src_party_id,
        'dest_party_id': dest_party_id,
        'src_role': src_role,
        'json_body': json_body,
        'headers': headers,
    }

    if federated_mode == FederatedMode.SINGLE or kwargs['dest_party_id'] == '0':
        kwargs.update({
            'host': RuntimeConfig.JOB_SERVER_HOST,
            'port': RuntimeConfig.HTTP_PORT,
        })

        return federated_coordination_on_http(**kwargs)

    if federated_mode == FederatedMode.MULTIPLE:
        host, port, protocol = get_federated_proxy_address(kwargs['src_party_id'], kwargs['dest_party_id'])
        kwargs.update({
            'host': host,
            'port': port,
        })

        if protocol == CoordinationCommunicationProtocol.HTTP:
            return federated_coordination_on_http(**kwargs)

        if protocol == CoordinationCommunicationProtocol.GRPC:
            return federated_coordination_on_grpc(**kwargs)

        raise Exception(f'{protocol} coordination communication protocol is not supported.')

    raise Exception(f'{federated_mode} work mode is not supported')


def local_api(job_id, method, endpoint, json_body):
    return federated_api(
        job_id=job_id, method=method, endpoint=endpoint, json_body=json_body,
        src_party_id=PARTY_ID, dest_party_id=PARTY_ID, src_role='',
        federated_mode=FederatedMode.SINGLE,
    )


def cluster_api(method, host, port, endpoint, json_body, headers=None):
    return federated_coordination_on_http(
        job_id='', method=method, host=host, port=port, endpoint=endpoint,
        json_body=json_body, headers=headers or request_headers.copy(),
    )


def get_federated_proxy_address(src_party_id, dest_party_id):
    src_party_id = str(src_party_id)
    dest_party_id = str(dest_party_id)

    if PROXY_PROTOCOL == "default":
        protocol = CoordinationCommunicationProtocol.HTTP
    else:
        protocol = PROXY_PROTOCOL

    if isinstance(PROXY, dict):
        proxy_name = PROXY.get("name", CoordinationProxyService.FATEFLOW)

        if proxy_name == CoordinationProxyService.FATEFLOW and src_party_id == dest_party_id:
            host = RuntimeConfig.JOB_SERVER_HOST
            port = RuntimeConfig.HTTP_PORT
        else:
            host = PROXY["host"]
            port = PROXY[f"{protocol}_port"]

        return (
            host,
            port,
            protocol,
        )

    if PROXY == CoordinationProxyService.ROLLSITE:
        proxy_address = ServerRegistry.FATE_ON_EGGROLL[CoordinationProxyService.ROLLSITE]

        return (
            proxy_address["host"],
            proxy_address.get("grpc_port", proxy_address["port"]),
            CoordinationCommunicationProtocol.GRPC,
        )

    if PROXY == CoordinationProxyService.NGINX:
        proxy_address = ServerRegistry.FATE_ON_SPARK[CoordinationProxyService.NGINX]

        return (
            proxy_address["host"],
            proxy_address[f"{protocol}_port"],
            protocol,
        )

    raise RuntimeError(f"can not support coordinate proxy {PROXY}")


def federated_coordination_on_http(
    job_id, method, host, port, endpoint,
    json_body, headers, **_,
):
    url = f'http://{host}:{port}/{API_VERSION}{endpoint}'

    timeout = JobDefaultConfig.remote_request_timeout or 0
    timeout = timeout / 1000 or None

    for t in range(REQUEST_TRY_TIMES):
        try:
            response = request(
                method=method, url=url, timeout=timeout,
                headers=headers, json=json_body,
            )
            response.raise_for_status()
        except Exception as e:
            schedule_logger(job_id).warning(f'http api error: {url}\n{e}')
            if t >= REQUEST_TRY_TIMES - 1:
                raise e
        else:
            audit_logger(job_id).info(f'http api response: {url}\n{response.text}')
            return response.json()

        time.sleep(get_exponential_backoff_interval(t))


def federated_coordination_on_grpc(
    job_id, method, host, port, endpoint,
    src_party_id, dest_party_id,
    json_body, headers, **_,
):
    endpoint = f"/{API_VERSION}{endpoint}"
    timeout = JobDefaultConfig.remote_request_timeout or 0

    _packet = wrap_grpc_packet(
        json_body=json_body, http_method=method, url=endpoint,
        src_party_id=src_party_id, dst_party_id=dest_party_id,
        job_id=job_id, headers=headers, overall_timeout=timeout,
    )
    _routing_metadata = gen_routing_metadata(
        src_party_id=src_party_id, dest_party_id=dest_party_id,
    )

    for t in range(REQUEST_TRY_TIMES):
        channel, stub = get_command_federation_channel(host, port)

        try:
            _return, _call = stub.unaryCall.with_call(
                _packet, metadata=_routing_metadata,
                timeout=timeout / 1000 or None,
            )
        except Exception as e:
            schedule_logger(job_id).warning(f'grpc api error: {endpoint}\n{e}')
            if t >= REQUEST_TRY_TIMES - 1:
                raise e
        else:
            audit_logger(job_id).info(f'grpc api response: {endpoint}\n{_return}')
            return json_loads(_return.body.value)
        finally:
            channel.close()

        time.sleep(get_exponential_backoff_interval(t))


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
    if not getattr(ServerRegistry, role.upper()):
        ServerRegistry.load()
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


def create_job_request_check(func):
    @wraps(func)
    def _wrapper(*_args, **_kwargs):
        party_id = _kwargs.get("party_id")
        role = _kwargs.get("role")
        body = flask_request.json
        headers = flask_request.headers
        src_role = headers.get("scr_role")
        src_party_id = headers.get("src_party_id")

        # permission check
        if PERMISSION_SWITCH:
            permission_return = HookManager.permission_check(get_permission_parameters(role, party_id, src_role,
                                                                                       src_party_id, body))
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
            input_arguments = flask_request.json or flask_request.form.to_dict()
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
    @wraps(func)
    def _route(*args, **kwargs):
        request_data = flask_request.json or flask_request.form.to_dict()

        instance_id = request_data.get('instance_id')
        if not instance_id:
            return func(*args, **kwargs)

        request_data['forward_times'] = int(request_data.get('forward_times', 0)) + 1
        if request_data['forward_times'] > 2:
            return error_response(429, 'Too many forwarding times.')

        instance = RuntimeConfig.SERVICE_DB.get_servers().get(instance_id)
        if instance is None:
            return error_response(404, 'Flow Instance not found.')

        if instance.http_address == f'{HOST}:{HTTP_PORT}':
            return func(*args, **kwargs)

        endpoint = flask_request.full_path
        prefix = f'/{API_VERSION}/'
        if endpoint.startswith(prefix):
            endpoint = endpoint[len(prefix) - 1:]

        response = cluster_api(
            method=flask_request.method,
            host=instance.host,
            port=instance.http_port,
            endpoint=endpoint,
            json_body=request_data,
            headers=flask_request.headers,
        )
        return get_json_result(**response)

    return _route


def is_localhost(ip):
    return ip in {'127.0.0.1', '::1', '[::1]', 'localhost'}


def send_file_in_mem(data, filename):
    if not isinstance(data, (str, bytes)):
        data = json_dumps(data)
    if isinstance(data, str):
        data = data.encode('utf-8')

    f = BytesIO()
    f.write(data)
    f.seek(0)

    return send_file(f, as_attachment=True, attachment_filename=filename)
