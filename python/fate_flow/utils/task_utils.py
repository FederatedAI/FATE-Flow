import functools

from flask import request as flask_request

from fate_flow.db.runtime_config import RuntimeConfig
from fate_flow.entity import RetCode
from fate_flow.operation.job_saver import JobSaver
from fate_flow.utils.api_utils import get_json_result
from fate_flow.utils.requests_utils import request


def task_request_proxy(func):
    @functools.wraps(func)
    def _wrapper(*args, **kwargs):
        party_id, role, task_id, task_version = kwargs.get("party_id"), kwargs.get("role"), \
                                                kwargs.get("task_id"), kwargs.get("task_version")
        tasks = JobSaver.query_task(task_id=task_id, task_version=task_version, role=role, party_id=int(party_id))
        if tasks:
            if tasks[0].f_run_ip and tasks[0].f_run_port:
                if tasks[0].f_run_ip != RuntimeConfig.JOB_SERVER_HOST:
                    source_url = flask_request.url
                    source_address = source_url.split("/")[2]
                    dest_address = ":".join([tasks[0].f_run_ip, str(tasks[0].f_run_port)])
                    dest_url = source_url.replace(source_address, dest_address)
                    response = request(method=flask_request.method, url=dest_url, json=flask_request.json, headers=flask_request.headers)
                    if response.status_code == 200:
                        response = response.json()
                        return get_json_result(retcode=response.get("retcode"), retmsg=response.get('retmsg'))
                    else:
                       return get_json_result(retcode = response.status_code, retmsg = response.text)
        else:
            return get_json_result(retcode=RetCode.DATA_ERROR, retmsg='no found task')
        return func(*args, **kwargs)
    return _wrapper
