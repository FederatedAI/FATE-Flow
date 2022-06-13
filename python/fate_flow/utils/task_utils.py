import functools

from flask import request as flask_request

from fate_flow.db.runtime_config import RuntimeConfig
from fate_flow.entity import RetCode
from fate_flow.operation.job_saver import JobSaver
from fate_flow.utils.api_utils import get_json_result
from fate_flow.utils.requests_utils import request


def task_request_proxy(party_id_index, role_index, task_id_index, task_version_index):
    def _out(func):
        @functools.wraps(func)
        def _wrapper(*_args, **_kwargs):
            path_list = flask_request.path.split("/")
            party_id, role, task_id, task_version = path_list[party_id_index], path_list[role_index], \
                                                    path_list[task_id_index], path_list[task_version_index]
            tasks = JobSaver.query_task(task_id=task_id, task_version=task_version, role=role, party_id=int(party_id))
            if tasks:
                if tasks[0].f_run_ip != RuntimeConfig.JOB_SERVER_HOST:
                    source_url = flask_request.url
                    source_address = source_url.split("/")[2]
                    dest_address = ":".join([tasks[0].f_run_ip, tasks[0].f_run_port])
                    dest_url = source_url.replace(source_address, dest_address)
                    response = request(method=flask_request.method, url=dest_url, json=flask_request.json, headers=flask_request.headers)
                    return response
                else:
                    return func(*_args, **_kwargs)
            else:
                return get_json_result(retcode=RetCode.DATA_ERROR, retmsg='no found task')
        return _wrapper
    return _out