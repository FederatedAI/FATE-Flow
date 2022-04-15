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
import io
import json
import os
import tarfile

from flask import abort, request, send_file

from fate_arch.common.base_utils import json_dumps, json_loads
from fate_flow.controller.job_controller import JobController
from fate_flow.entity import JobConfigurationBase, RetCode
from fate_flow.entity.run_status import FederatedSchedulingStatusCode, JobStatus
from fate_flow.operation.job_clean import JobClean
from fate_flow.operation.job_saver import JobSaver
from fate_flow.operation.job_tracker import Tracker
from fate_flow.scheduler.dag_scheduler import DAGScheduler
from fate_flow.scheduler.federated_scheduler import FederatedScheduler
from fate_flow.settings import TEMP_DIRECTORY, stat_logger
from fate_flow.utils import detect_utils, job_utils, log_utils, schedule_utils
from fate_flow.utils.api_utils import error_response, get_json_result
from fate_flow.utils.config_adapter import JobRuntimeConfigAdapter
from fate_flow.utils.log_utils import schedule_logger


@manager.route('/submit', methods=['POST'])
def submit_job():
    submit_result = DAGScheduler.submit(JobConfigurationBase(**request.json))
    return get_json_result(retcode=submit_result["code"], retmsg=submit_result["message"],
                           job_id=submit_result["job_id"],
                           data=submit_result if submit_result["code"] == RetCode.SUCCESS else None)


@manager.route('/stop', methods=['POST'])
def stop_job():
    job_id = request.json.get('job_id')
    stop_status = request.json.get("stop_status", "canceled")
    jobs = JobSaver.query_job(job_id=job_id)
    if jobs:
        schedule_logger(job_id).info(f"stop job on this party")
        kill_status, kill_details = JobController.stop_jobs(job_id=job_id, stop_status=stop_status)
        schedule_logger(job_id).info(f"stop job on this party status {kill_status}")
        schedule_logger(job_id).info(f"request stop job to {stop_status}")
        status_code, response = FederatedScheduler.request_stop_job(job=jobs[0], stop_status=stop_status, command_body=jobs[0].to_dict())
        if status_code == FederatedSchedulingStatusCode.SUCCESS:
            return get_json_result(retcode=RetCode.SUCCESS, retmsg=f"stop job on this party {kill_status}; stop job on all party success")
        else:
            return get_json_result(retcode=RetCode.OPERATING_ERROR, retmsg=f"stop job on this party {kill_status}", data=response)
    else:
        schedule_logger(job_id).info(f"can not found job to stop")
        return get_json_result(retcode=RetCode.DATA_ERROR, retmsg="can not found job")


@manager.route('/rerun', methods=['POST'])
def rerun_job():
    job_id = request.json.get("job_id")
    jobs = JobSaver.query_job(job_id=job_id)
    if jobs:
        status_code, response = FederatedScheduler.request_rerun_job(job=jobs[0], command_body=request.json)
        if status_code == FederatedSchedulingStatusCode.SUCCESS:
            return get_json_result(retcode=RetCode.SUCCESS, retmsg="rerun job success")
        else:
            return get_json_result(retcode=RetCode.OPERATING_ERROR, retmsg="rerun job failed:\n{}".format(json_dumps(response)))
    else:
        return get_json_result(retcode=RetCode.DATA_ERROR, retmsg="can not found job")


@manager.route('/query', methods=['POST'])
def query_job():
    jobs = JobSaver.query_job(**request.json)
    if not jobs:
        return get_json_result(retcode=0, retmsg='no job could be found', data=[])
    return get_json_result(retcode=0, retmsg='success', data=[job.to_dict() for job in jobs])


@manager.route('/list/job', methods=['POST'])
def list_job():
    limit, offset = parse_limit_and_offset()

    query = {
        'tag': ('!=', 'submit_failed'),
    }

    for i in ('job_id', 'description'):
        if request.json.get(i) is not None:
            query[i] = ('contains', request.json[i])
    if request.json.get('party_id') is not None:
        try:
            query['party_id'] = int(request.json['party_id'])
        except Exception:
            return error_response(400, f"Invalid parameter 'party_id'.")
        query['party_id'] = ('contains', query['party_id'])
    if request.json.get('partner') is not None:
        query['roles'] = ('contains', query['partner'])

    for i in ('role', 'status'):
        if request.json.get(i) is None:
            continue

        if isinstance(request.json[i], str):
            request.json[i] = [request.json[i]]
        if not isinstance(request.json[i], list):
            return error_response(400, f"Invalid parameter '{i}'.")
        request.json[i] = set(request.json[i])

        for j in request.json[i]:
            if j not in valid_query_parameters[i]:
                return error_response(400, f"Invalid parameter '{i}'.")
        query[i] = ('in_', request.json[i])

    jobs, count = job_utils.list_job(limit, offset, query, parse_order_by(('create_time', 'desc')))
    jobs = [job.to_human_model_dict() for job in jobs]

    for job in jobs:
        job['party_id'] = int(job['party_id'])

        job['partners'] = set()
        for i in ('guest', 'host', 'arbiter'):
            job['partners'].update(job['roles'].get(i, []))
        job['partners'].discard(job['party_id'])
        job['partners'] = sorted(job['partners'])

    return get_json_result(data={
        'jobs': jobs,
        'count': count,
    })


@manager.route('/update', methods=['POST'])
def update_job():
    job_info = request.json
    jobs = JobSaver.query_job(job_id=job_info['job_id'], party_id=job_info['party_id'], role=job_info['role'])
    if not jobs:
        return get_json_result(retcode=101, retmsg='find job failed')
    else:
        JobSaver.update_job(job_info={'description': job_info.get('notes', ''), 'job_id': job_info['job_id'], 'role': job_info['role'],
                                      'party_id': job_info['party_id']})
        return get_json_result(retcode=0, retmsg='success')


@manager.route('/parameter/update', methods=['POST'])
@detect_utils.validate_request("job_id")
def update_parameters():
    job_info = request.json
    component_parameters = job_info.pop("component_parameters", None)
    job_parameters = job_info.pop("job_parameters", None)
    job_info["is_initiator"] = True
    jobs = JobSaver.query_job(**job_info)
    if not jobs:
        return get_json_result(retcode=RetCode.DATA_ERROR, retmsg=log_utils.failed_log(f"query job by {job_info}"))
    else:
        retcode, retdata = DAGScheduler.update_parameters(jobs[0], job_parameters, component_parameters)
        return get_json_result(retcode=retcode, data=retdata)


@manager.route('/config', methods=['POST'])
def job_config():
    jobs = JobSaver.query_job(**request.json)
    if not jobs:
        return get_json_result(retcode=101, retmsg='find job failed')
    else:
        job = jobs[0]
        response_data = dict()
        response_data['job_id'] = job.f_job_id
        response_data['dsl'] = job.f_dsl
        response_data['runtime_conf'] = job.f_runtime_conf
        response_data['train_runtime_conf'] = job.f_train_runtime_conf

        adapter = JobRuntimeConfigAdapter(job.f_runtime_conf)
        job_parameters = adapter.get_common_parameters().to_dict()
        response_data['model_info'] = {'model_id': job_parameters.get('model_id'),
                                       'model_version': job_parameters.get('model_version')}
        return get_json_result(retcode=0, retmsg='success', data=response_data)


def check_job_log_dir():
    job_id = str(request.json['job_id'])
    job_log_dir = job_utils.get_job_log_directory(job_id=job_id)

    if not os.path.exists(job_log_dir):
        abort(error_response(404, f"Log file path: '{job_log_dir}' not found. Please check if the job id is valid."))

    return job_id, job_log_dir


@manager.route('/log/download', methods=['POST'])
@detect_utils.validate_request('job_id')
def job_log_download():
    job_id, job_log_dir = check_job_log_dir()

    memory_file = io.BytesIO()
    tar = tarfile.open(fileobj=memory_file, mode='w:gz')
    for root, dir, files in os.walk(job_log_dir):
        for file in files:
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, job_log_dir)
            tar.add(full_path, rel_path)

    tar.close()
    memory_file.seek(0)
    return send_file(memory_file, attachment_filename=f'job_{job_id}_log.tar.gz', as_attachment=True)


@manager.route('/log/path', methods=['POST'])
@detect_utils.validate_request('job_id')
def job_log_path():
    job_id, job_log_dir = check_job_log_dir()

    return get_json_result(data={"logs_directory": job_log_dir})


@manager.route('/task/query', methods=['POST'])
def query_task():
    tasks = JobSaver.query_task(**request.json)
    if not tasks:
        return get_json_result(retcode=101, retmsg='find task failed')
    return get_json_result(retcode=0, retmsg='success', data=[task.to_dict() for task in tasks])


@manager.route('/list/task', methods=['POST'])
def list_task():
    limit, offset = parse_limit_and_offset()

    query = {}
    for i in ('job_id', 'role', 'party_id', 'component_name'):
        if request.json.get(i) is not None:
            query[i] = request.json[i]
    if query.get('role') is not None:
        if query['role'] not in valid_query_parameters['role']:
            return error_response(400, f"Invalid parameter 'role'.")
    if query.get('party_id') is not None:
        try:
            query['party_id'] = int(query['party_id'])
        except Exception:
            return error_response(400, f"Invalid parameter 'party_id'.")

    tasks, count = job_utils.list_task(limit, offset, query, parse_order_by(('create_time', 'asc')))
    return get_json_result(data={
        'tasks': [task.to_human_model_dict() for task in tasks],
        'count': count,
    })


@manager.route('/data/view/query', methods=['POST'])
def query_component_output_data_info():
    output_data_infos = Tracker.query_output_data_infos(**request.json)
    if not output_data_infos:
        return get_json_result(retcode=101, retmsg='find data view failed')
    return get_json_result(retcode=0, retmsg='success', data=[output_data_info.to_dict() for output_data_info in output_data_infos])


@manager.route('/clean', methods=['POST'])
def clean_job():
    JobClean.start_clean_job(**request.json)
    return get_json_result(retcode=0, retmsg='success')


@manager.route('/clean/queue', methods=['POST'])
def clean_queue():
    jobs = JobSaver.query_job(is_initiator=True, status=JobStatus.WAITING)
    clean_status = {}
    for job in jobs:
        status_code, response = FederatedScheduler.request_stop_job(job=job, stop_status=JobStatus.CANCELED)
        clean_status[job.f_job_id] = status_code
    return get_json_result(retcode=0, retmsg='success', data=clean_status)


@manager.route('/dsl/generate', methods=['POST'])
def dsl_generator():
    data = request.json
    cpn_str = data.get("cpn_str", "")
    try:
        if not cpn_str:
            raise Exception("Component list should not be empty.")
        if isinstance(cpn_str, list):
            cpn_list = cpn_str
        else:
            if (cpn_str.find("/") and cpn_str.find("\\")) != -1:
                raise Exception("Component list string should not contain '/' or '\\'.")
            cpn_str = cpn_str.replace(" ", "").replace("\n", "").strip(",[]")
            cpn_list = cpn_str.split(",")
        train_dsl = json_loads(data.get("train_dsl"))
        parser = schedule_utils.get_dsl_parser_by_version(data.get("version", "2"))
        predict_dsl = parser.deploy_component(cpn_list, train_dsl)

        if data.get("filename"):
            os.makedirs(TEMP_DIRECTORY, exist_ok=True)
            temp_filepath = os.path.join(TEMP_DIRECTORY, data.get("filename"))
            with open(temp_filepath, "w") as fout:
                fout.write(json.dumps(predict_dsl, indent=4))
            return send_file(open(temp_filepath, 'rb'), as_attachment=True, attachment_filename=data.get("filename"))
        return get_json_result(data=predict_dsl)
    except Exception as e:
        stat_logger.exception(e)
        return error_response(210, "DSL generating failed. For more details, "
                                   "please check logs/fate_flow/fate_flow_stat.log.")


@manager.route('/url/get', methods=['POST'])
@detect_utils.validate_request('job_id', 'role', 'party_id')
def get_url():
    request_data = request.json
    jobs = JobSaver.query_job(job_id=request_data.get('job_id'), role=request_data.get('role'),
                              party_id=request_data.get('party_id'))
    if jobs:
        board_urls = []
        for job in jobs:
            board_url = job_utils.get_board_url(job.f_job_id, job.f_role, job.f_party_id)
            board_urls.append(board_url)
        return get_json_result(data={'board_url': board_urls})
    else:
        return get_json_result(retcode=101, retmsg='no found job')


def parse_limit_and_offset():
    try:
        limit = int(request.json.get('limit', 0))
        page = int(request.json.get('page', 1)) - 1
    except Exception:
        abort(error_response(400, f"Invalid parameter 'limit' or 'page'."))

    return limit, limit * page


def parse_order_by(default=None):
    order_by = []

    if request.json.get('order_by') is not None:
        if request.json['order_by'] not in valid_query_parameters['order_by']:
            abort(error_response(400, f"Invalid parameter 'order_by'."))
        order_by.append(request.json['order_by'])

        if request.json.get('order') is not None:
            if request.json['order'] not in valid_query_parameters['order']:
                abort(error_response(400, f"Invalid parameter order 'order'."))
            order_by.append(request.json['order'])

    return order_by or default


valid_query_parameters = {
    'role': {'guest', 'host', 'arbiter', 'local'},
    'status': {'success', 'running', 'waiting', 'failed', 'canceled'},
    'order_by': {'job_id', 'create_time', 'start_time', 'end_time', 'elapsed'},
    'order': {'asc', 'desc'},
}
