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

from fate_flow.controller.job import JobController
from fate_flow.controller.task import TaskController
from fate_flow.entity.types import TaskStatus
from fate_flow.entity.code import ReturnCode
from fate_flow.errors.server_error import CreateJobFailed, UpdateJobFailed, KillFailed, JobResourceException,\
    NoFoundTask, StartTaskFailed, UpdateTaskFailed, KillTaskFailed, TaskResourceException
from fate_flow.manager.service.resource_manager import ResourceManager
from fate_flow.manager.operation.job_saver import JobSaver
from fate_flow.utils.api_utils import API, stat_logger
from fate_flow.utils.permission_utils import create_job_request_check
from fate_flow.utils.wraps_utils import task_request_proxy

page_name = 'partner'


@manager.route('/job/create', methods=['POST'])
@API.Input.json(dag=fields.Dict(required=True))
@API.Input.json(schema_version=fields.String(required=True))
@API.Input.json(job_id=fields.String(required=True))
@API.Input.json(role=fields.String(required=True))
@API.Input.json(party_id=fields.String(required=True))
@create_job_request_check
def partner_create_job(dag, schema_version, job_id, role, party_id):
    try:
        JobController.create_job(dag, schema_version, job_id, role, party_id)
        return API.Output.json()
    except Exception as e:
        stat_logger.exception(e)
        return API.Output.fate_flow_exception(CreateJobFailed(detail=str(e)))


@manager.route('/job/start', methods=['POST'])
@API.Input.json(job_id=fields.String(required=True))
@API.Input.json(role=fields.String(required=True))
@API.Input.json(party_id=fields.String(required=True))
@API.Input.json(extra_info=fields.Dict(required=False))
def start_job(job_id, role, party_id, extra_info=None):
    JobController.start_job(job_id=job_id, role=role, party_id=party_id, extra_info=extra_info)
    return API.Output.json()


@manager.route('/job/status/update', methods=['POST'])
@API.Input.json(job_id=fields.String(required=True))
@API.Input.json(role=fields.String(required=True))
@API.Input.json(party_id=fields.String(required=True))
@API.Input.json(status=fields.String(required=True))
def partner_job_status_update(job_id, role, party_id, status):
    job_info = {
        "job_id": job_id,
        "role": role,
        "party_id": party_id,
        "status": status
    }
    if JobController.update_job_status(job_info=job_info):
        return API.Output.json(code=ReturnCode.Base.SUCCESS, message='success')
    else:
        return API.Output.fate_flow_exception(UpdateJobFailed(
            job_id=job_id, role=role, party_id=party_id, status=status
        ))


@manager.route('/job/update', methods=['POST'])
@API.Input.json(job_id=fields.String(required=True))
@API.Input.json(role=fields.String(required=True))
@API.Input.json(party_id=fields.String(required=True))
@API.Input.json(progress=fields.Float())
def partner_job_update(job_id, role, party_id, progress):
    job_info = {
        "job_id": job_id,
        "role": role,
        "party_id": party_id
    }
    if progress:
        job_info.update({"progress": progress})
    if JobController.update_job(job_info=job_info):
        return API.Output.json(code=ReturnCode.Base.SUCCESS, message='success')
    else:
        return API.Output.fate_flow_exception(UpdateJobFailed(**job_info))


@manager.route('/job/resource/apply', methods=['POST'])
@API.Input.json(job_id=fields.String(required=True))
@API.Input.json(role=fields.String(required=True))
@API.Input.json(party_id=fields.String(required=True))
def apply_resource(job_id, role, party_id):
    status = ResourceManager.apply_for_job_resource(job_id, role, party_id)
    if status:
        return API.Output.json(code=ReturnCode.Base.SUCCESS, message='success')
    else:
        return API.Output.fate_flow_exception(JobResourceException(
            job_id=job_id, role=role, party_id=party_id,
            operation_type="apply"
        ))


@manager.route('/job/resource/return', methods=['POST'])
@API.Input.json(job_id=fields.String(required=True))
@API.Input.json(role=fields.String(required=True))
@API.Input.json(party_id=fields.String(required=True))
def return_resource(job_id, role, party_id):
    status = ResourceManager.return_job_resource(job_id=job_id, role=role, party_id=party_id)
    if status:
        return API.Output.json(ReturnCode.Base.SUCCESS, message='success')
    else:
        return API.Output.fate_flow_exception(JobResourceException(
            job_id=job_id, role=role, party_id=party_id,
            operation_type="return"
        ))


@manager.route('/job/stop', methods=['POST'])
@API.Input.json(job_id=fields.String(required=True))
@API.Input.json(role=fields.String(required=True))
@API.Input.json(party_id=fields.String(required=True))
def stop_job(job_id, role, party_id):
    kill_status, kill_details = JobController.stop_jobs(job_id=job_id, role=role, party_id=party_id)
    if kill_status:
        return API.Output.json()
    return API.Output.fate_flow_exception(KillFailed(detail=kill_details))


@manager.route('/task/resource/apply', methods=['POST'])
@API.Input.json(job_id=fields.String(required=True))
@API.Input.json(role=fields.String(required=True))
@API.Input.json(party_id=fields.String(required=True))
@API.Input.json(task_id=fields.String(required=True))
@API.Input.json(task_version=fields.Integer(required=True))
def apply_task_resource(job_id, role, party_id, task_id, task_version):
    status = ResourceManager.apply_for_task_resource(job_id=job_id, role=role, party_id=party_id,
                                                     task_id=task_id, task_version=task_version)
    if status:
        return API.Output.json(code=ReturnCode.Base.SUCCESS, message='success')
    else:
        return API.Output.fate_flow_exception(TaskResourceException(
            job_id=job_id, role=role, party_id=party_id,
            task_id=task_id, task_version=task_version, operation_type="apply"
        ))


@manager.route('/task/resource/return', methods=['POST'])
@API.Input.json(job_id=fields.String(required=True))
@API.Input.json(role=fields.String(required=True))
@API.Input.json(party_id=fields.String(required=True))
@API.Input.json(task_id=fields.String(required=True))
@API.Input.json(task_version=fields.Integer(required=True))
def return_task_resource(job_id, role, party_id, task_id, task_version):
    status = ResourceManager.return_task_resource(job_id=job_id, role=role, party_id=party_id,
                                                  task_id=task_id, task_version=task_version)
    if status:
        return API.Output.json(ReturnCode.Base.SUCCESS, message='success')
    else:
        return API.Output.fate_flow_exception(TaskResourceException(
            job_id=job_id, role=role, party_id=party_id, task_id=task_id,
            task_version=task_version,  operation_type="return"
        ))


@manager.route('/task/start', methods=['POST'])
@API.Input.json(job_id=fields.String(required=True))
@API.Input.json(role=fields.String(required=True))
@API.Input.json(party_id=fields.String(required=True))
@API.Input.json(task_id=fields.String(required=True))
@API.Input.json(task_version=fields.Integer(required=True))
@task_request_proxy(filter_local=True)
def start_task(job_id, role, party_id, task_id, task_version):
    task = JobSaver.query_task(task_id=task_id, task_version=task_version, role=role, party_id=party_id)[0]
    if not task:
        return API.Output.fate_flow_exception(
            NoFoundTask(job_id=job_id, role=role, party_id=party_id, task_id=task_id, task_version=task_version)
        )
    if TaskController.start_task(task):
        return API.Output.json(code=ReturnCode.Base.SUCCESS, message='success')
    else:
        return API.Output.fate_flow_exception(StartTaskFailed(
            job_id=job_id, role=role, party_id=party_id,
            task_id=task_id, task_version=task_version
        ))


@manager.route('/task/collect', methods=['POST'])
@API.Input.json(job_id=fields.String(required=True))
@API.Input.json(role=fields.String(required=True))
@API.Input.json(party_id=fields.String(required=True))
@API.Input.json(task_id=fields.String(required=True))
@API.Input.json(task_version=fields.Integer(required=True))
def collect_task(job_id, role, party_id, task_id, task_version):
    task_info = TaskController.collect_task(job_id=job_id, task_id=task_id, task_version=task_version, role=role,
                                            party_id=party_id)
    if task_info:
        return API.Output.json(code=ReturnCode.Base.SUCCESS, message="success", data=task_info)
    else:
        return API.Output.fate_flow_exception(NoFoundTask(job_id=job_id, role=role, party_id=party_id,
                                                          task_id=task_id, task_version=task_version))


@manager.route('/task/status/update', methods=['POST'])
@API.Input.json(job_id=fields.String(required=True))
@API.Input.json(role=fields.String(required=True))
@API.Input.json(party_id=fields.String(required=True))
@API.Input.json(task_id=fields.String(required=True))
@API.Input.json(task_version=fields.Integer(required=True))
@API.Input.json(status=fields.String(required=True))
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
        return API.Output.json()
    else:
        return API.Output.fate_flow_exception(UpdateTaskFailed(
            job_id=job_id, role=role, party_id=party_id,
            task_id=task_id, task_version=task_version, status=status)
        )


@manager.route('/task/stop', methods=['POST'])
@API.Input.json(job_id=fields.String(required=True))
@API.Input.json(role=fields.String(required=True))
@API.Input.json(party_id=fields.String(required=True))
@API.Input.json(task_id=fields.String(required=True))
@API.Input.json(task_version=fields.Integer(required=True))
@API.Input.json(status=fields.String())
@task_request_proxy()
def stop_task(job_id, role, party_id, task_id, task_version, status=None):
    if not status:
        status = TaskStatus.FAILED
    tasks = JobSaver.query_task(job_id=job_id, task_id=task_id, task_version=task_version, role=role, party_id=party_id)
    kill_status = True
    for task in tasks:
        kill_status = kill_status & TaskController.stop_task(task=task, stop_status=status)
    if kill_status:
        return API.Output.json()
    else:
        return API.Output.fate_flow_exception(KillTaskFailed(job_id=job_id, role=role, party_id=party_id,
                                                             task_id=task_id, task_version=task_version))


@manager.route('/task/rerun', methods=['POST'])
@API.Input.json(job_id=fields.String(required=True))
@API.Input.json(role=fields.String(required=True))
@API.Input.json(party_id=fields.String(required=True))
@API.Input.json(task_id=fields.String(required=True))
@API.Input.json(task_version=fields.Integer(required=True))
@API.Input.json(new_version=fields.Integer(required=True))
def rerun_task(job_id, role, party_id, task_id, task_version, new_version):
    tasks = JobSaver.query_task(job_id=job_id, task_id=task_id, role=role, party_id=party_id)
    if tasks:
        TaskController.create_new_version_task(task=tasks[0], new_version=new_version)
    return API.Output.json()
