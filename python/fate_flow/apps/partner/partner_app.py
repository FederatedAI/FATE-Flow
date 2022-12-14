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
from webargs import fields

from fate_flow.controller.job_controller import JobController
from fate_flow.controller.task_controller import TaskController
from fate_flow.entity import RetCode
from fate_flow.entity.run_status import TaskStatus
from fate_flow.operation.job_saver import JobSaver
from fate_flow.utils.api_utils import get_json_result, validate_request_json, job_request_json, task_request_json

page_name = 'partner'


@manager.route('/job/create', methods=['POST'])
@job_request_json(dag_schema=fields.Dict(required=True))
def partner_create_job(dag_schema, job_id, role, party_id):
    try:
        JobController.create_job(dag_schema, job_id, role, party_id)
        return get_json_result()
    except RuntimeError as e:
        return get_json_result(code=RetCode.OPERATING_ERROR, message=str(e), data={"job_id": job_id})


@manager.route('/job/start', methods=['POST'])
@job_request_json(extra_info=fields.Dict(required=False))
def start_job(job_id, role, party_id, extra_info=None):
    JobController.start_job(job_id=job_id, role=role, party_id=party_id, extra_info=extra_info)
    return get_json_result(code=0, message='success')


@manager.route('/job/status/update', methods=['POST'])
@job_request_json(status=fields.String(required=True))
def partner_job_status_update(job_id, role, party_id, status):
    job_info = {
        "job_id": job_id,
        "role": role,
        "party_id": party_id,
        "status": status
    }
    if JobController.update_job_status(job_info=job_info):
        return get_json_result(code=0, message='success')
    else:
        return get_json_result(code=RetCode.NOT_EFFECTIVE, message="update job status does not take effect")


@manager.route('/job/update', methods=['POST'])
@job_request_json(progress=fields.Float())
def partner_job_update(job_id, role, party_id, progress):
    job_info = {
        "job_id": job_id,
        "role": role,
        "party_id": party_id
    }
    if progress:
        job_info.update({"progress": progress})
    JobController.update_job(job_info=job_info)
    return get_json_result(code=0, message='success')


@manager.route('/job/pipeline/save', methods=['POST'])
@job_request_json()
def save_pipeline(job_id, role, party_id):
    return get_json_result(code=0, message='success')


@manager.route('/job/resource/apply', methods=['POST'])
@job_request_json()
def apply_resource(job_id, role, party_id):
    return get_json_result(code=0, message='success')


@manager.route('/job/resource/return', methods=['POST'])
@job_request_json()
def return_resource(job_id, role, party_id):
    return get_json_result(code=0, message='success')


@manager.route('/job/stop', methods=['POST'])
@job_request_json()
def stop_job(job_id, role, party_id):
    kill_status, kill_details = JobController.stop_jobs(job_id=job_id, role=role, party_id=party_id)
    return get_json_result(code=RetCode.SUCCESS if kill_status else RetCode.EXCEPTION_ERROR,
                           message='success' if kill_status else 'failed',
                           data=kill_details)


@manager.route('/task/start', methods=['POST'])
@task_request_json()
def start_task(job_id, role, party_id, task_id, task_version):
    TaskController.start_task(job_id, role, party_id, task_id, task_version)
    return get_json_result(code=0, message='success')


@manager.route('/task/collect', methods=['POST'])
@task_request_json()
def collect_task(job_id, role, party_id, task_id, task_version):
    task_info = TaskController.collect_task(job_id=job_id, task_id=task_id, task_version=task_version, role=role,
                                            party_id=party_id)
    if task_info:
        return get_json_result(code=RetCode.SUCCESS, message="success", data=task_info)
    else:
        return get_json_result(code=RetCode.OPERATING_ERROR, message="query task failed")


@manager.route('/task/status/update', methods=['POST'])
@task_request_json(status=fields.String(required=True))
def task_status_update(job_id, role, party_id, task_id, task_version, status):
    task_info = {}
    task_info.update({
        "job_id": job_id,
        "task_id": task_id,
        "task_version": task_version,
        "role": role,
        "party_id": party_id,
        "status": status
    })
    if TaskController.update_task_status(task_info=task_info):
        return get_json_result(code=0, message='success')
    else:
        return get_json_result(code=RetCode.NOT_EFFECTIVE, message="update job status does not take effect")


@manager.route('/task/stop', methods=['POST'])
@task_request_json(status=fields.String())
def stop_task(job_id, role, party_id, task_id, task_version, status=None):
    if not status:
        status = TaskStatus.FAILED
    tasks = JobSaver.query_task(job_id=job_id, task_id=task_id, task_version=task_version, role=role, party_id=party_id)
    kill_status = True
    for task in tasks:
        kill_status = kill_status & TaskController.stop_task(task=task, stop_status=status)
    return get_json_result(code=RetCode.SUCCESS if kill_status else RetCode.EXCEPTION_ERROR,
                           message='success' if kill_status else 'failed')