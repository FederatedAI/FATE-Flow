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
import threading
from functools import wraps

from fate_flow.entity.code import ReturnCode

from flask import request as flask_request
from fate_flow.errors.job import NoFoundTask, ResponseException, NoFoundINSTANCE
from fate_flow.operation.job_saver import JobSaver
from fate_flow.runtime.runtime_config import RuntimeConfig
from fate_flow.runtime.system_settings import HOST, HTTP_PORT, API_VERSION
from fate_flow.utils.api_utils import API, federated_coordination_on_http
from fate_flow.utils.log_utils import schedule_logger
from fate_flow.utils.requests_utils import request
from fate_flow.utils.schedule_utils import schedule_signal


def filter_parameters(filter_value=None):
    def _inner(func):
        @wraps(func)
        def _wrapper(*args, **kwargs):
            _kwargs = {}
            for k, v in kwargs.items():
                if v != filter_value:
                    _kwargs[k] = v
            return func(*args, **_kwargs)
        return _wrapper
    return _inner


def switch_function(switch, code=ReturnCode.Server.FUNCTION_RESTRICTED, message="function restricted"):
    def _inner(func):
        @wraps(func)
        def _wrapper(*args, **kwargs):
            if switch:
                return func(*args, **kwargs)
            else:
                raise Exception(code, f"func {func.__name__}, {message}")
        return _wrapper
    return _inner


def task_request_proxy(filter_local=False, force=True):
    def _outer(func):
        @wraps(func)
        def _wrapper(*args, **kwargs):
            party_id, role, task_id, task_version = kwargs.get("party_id"), kwargs.get("role"), \
                                                    kwargs.get("task_id"), kwargs.get("task_version")
            if not filter_local or (filter_local and role == "local"):
                tasks = JobSaver.query_task(task_id=task_id, task_version=task_version, role=role, party_id=party_id)
                if tasks:
                    if tasks[0].f_run_ip and tasks[0].f_run_port:
                        if tasks[0].f_run_ip != RuntimeConfig.JOB_SERVER_HOST:
                            source_url = flask_request.url
                            source_address = source_url.split("/")[2]
                            dest_address = ":".join([tasks[0].f_run_ip, str(tasks[0].f_run_port)])
                            dest_url = source_url.replace(source_address, dest_address)
                            try:
                                response = request(method=flask_request.method, url=dest_url, json=flask_request.json,
                                                   headers=flask_request.headers, params=flask_request.args)
                                if 200 <= response.status_code < 300:
                                    response = response.json()
                                    return API.Output.json(code=response.get("code"), message=response.get("message"))
                                else:
                                    raise ResponseException(response=response.text)
                            except Exception as e:
                                if force:
                                    return func(*args, **kwargs)
                                raise e
                else:
                    return API.Output.fate_flow_exception(NoFoundTask(
                        role=role,
                        party_id=party_id,
                        task_id=task_id,
                        task_version=task_version
                    ))
            return func(*args, **kwargs)
        return _wrapper
    return _outer


def cluster_route(func):
    @wraps(func)
    def _route(*args, **kwargs):
        instance_id = kwargs.get('instance_id')
        request_data = flask_request.json or flask_request.form.to_dict()
        if not instance_id:
            return func(*args, **kwargs)
        instance = RuntimeConfig.SERVICE_DB.get_servers().get(instance_id)
        if instance is None:
            return API.Output.fate_flow_exception(NoFoundINSTANCE(instance_id=instance_id))

        if instance.http_address == f'{HOST}:{HTTP_PORT}':
            return func(*args, **kwargs)

        endpoint = flask_request.full_path
        prefix = f'/{API_VERSION}/'
        if endpoint.startswith(prefix):
            endpoint = endpoint[len(prefix) - 1:]
        response = federated_coordination_on_http(
            method=flask_request.method,
            host=instance.host,
            port=instance.http_port,
            endpoint=endpoint,
            json_body=request_data,
            headers=flask_request.headers,
        )
        return API.Output.json(**response)
    return _route


def schedule_lock(func):
    @wraps(func)
    def _wrapper(*args, **kwargs):
        _lock = kwargs.pop("lock", False)
        if _lock:
            job = kwargs.get("job")
            schedule_logger(job.f_job_id).debug(f"get job {job.f_job_id} schedule lock")
            _result = None
            if not schedule_signal(job_id=job.f_job_id, set_or_reset=True):
                schedule_logger(job.f_job_id).warn(f"get job {job.f_job_id} schedule lock failed, "
                                                   f"job may be handled by another scheduler")
                return
            try:
                _result = func(*args, **kwargs)
            except Exception as e:
                raise e
            finally:
                schedule_signal(job_id=job.f_job_id, set_or_reset=False)
                schedule_logger(job.f_job_id).debug(f"release job {job.f_job_id} schedule lock")
                return _result
        else:
            return func(*args, **kwargs)
    return _wrapper


def threading_lock(func):
    @wraps(func)
    def _wrapper(*args, **kwargs):
        with threading.Lock():
            schedule_logger('wzh').info(f'{func.__name__}, args: {args}, kwargs: {kwargs}')
            return func(*args, **kwargs)
    return _wrapper