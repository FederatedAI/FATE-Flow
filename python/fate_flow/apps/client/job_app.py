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
import os
import tarfile

from webargs import fields

from fate_flow.controller.job_controller import JobController
from fate_flow.entity.code import ReturnCode
from fate_flow.errors.job import NoFoundJob, NoFoundTask, FileNoFound
from fate_flow.utils import job_utils
from fate_flow.utils.api_utils import API


@manager.route('/submit', methods=['POST'])
@API.Input.json(dag_schema=fields.Dict(required=True))
@API.Input.headers(user_name=fields.String(required=False))
def submit_job(dag_schema, user_name=None):
    submit_result = JobController.request_create_job(dag_schema, user_name)
    return API.Output.json(**submit_result)


@manager.route('/query', methods=['GET'])
@API.Input.params(job_id=fields.String(required=False))
@API.Input.params(role=fields.String(required=False))
@API.Input.params(party_id=fields.String(required=False))
@API.Input.params(status=fields.String(required=False))
@API.Input.headers(user_name=fields.String(required=False))
def query_job(job_id=None, role=None, party_id=None, status=None, user_name=None):
    jobs = JobController.query_job(job_id=job_id, role=role, party_id=party_id, status=status, user_name=user_name)
    if not jobs:
        return API.Output.fate_flow_exception(NoFoundJob(job_id=job_id, role=role, party_id=party_id, status=status))
    return API.Output.json(data=[job.to_human_model_dict() for job in jobs])


@manager.route('/stop', methods=['POST'])
@API.Input.json(job_id=fields.String(required=True))
def request_stop_job(job_id=None):
    stop_result = JobController.request_stop_job(job_id=job_id)
    return API.Output.json(**stop_result)


@manager.route('/rerun', methods=['POST'])
@API.Input.json(job_id=fields.String(required=True))
def request_rerun_job(job_id=None):
    jobs = JobController.query_job(job_id=job_id)
    if not jobs:
        return API.Output.fate_flow_exception(NoFoundJob(job_id=job_id))
    rerun_result = JobController.request_rerun_job(job=jobs[0])
    return API.Output.json(**rerun_result)


@manager.route('/list/query', methods=['GET'])
@API.Input.params(limit=fields.Integer(required=False))
@API.Input.params(page=fields.Integer(required=False))
@API.Input.params(job_id=fields.String(required=False))
@API.Input.params(description=fields.String(required=False))
@API.Input.params(partner=fields.String(required=False))
@API.Input.params(party_id=fields.String(required=False))
@API.Input.params(role=fields.Dict(required=False))
@API.Input.params(status=fields.Dict(required=False))
@API.Input.params(order_by=fields.String(required=False))
@API.Input.params(order=fields.String(required=False))
@API.Input.headers(user_name=fields.String(required=False))
def query_job_list(limit=0, page=0, job_id=None, description=None, partner=None, party_id=None, role=None, status=None,
                   order_by=None, order=None, user_name=None):
    count, data = JobController.query_job_list(
        limit, page, job_id, description, partner, party_id, role, status, order_by, order, user_name
    )
    return API.Output.json(code=ReturnCode.Base.SUCCESS, message="success",
                           data={"count": count, "data": data})


@manager.route('/task/query', methods=['GET'])
@API.Input.params(job_id=fields.String(required=False))
@API.Input.params(role=fields.String(required=False))
@API.Input.params(party_id=fields.String(required=False))
@API.Input.params(status=fields.String(required=False))
@API.Input.params(task_name=fields.String(required=False))
@API.Input.params(task_id=fields.String(required=False))
@API.Input.params(task_version=fields.Integer(required=False))
def query_task(job_id=None, role=None, party_id=None, status=None, task_name=None, task_id=None, task_version=None):
    tasks = JobController.query_tasks(job_id=job_id, role=role, party_id=party_id, status=status, task_name=task_name,
                                      task_id=task_id, task_version=task_version)
    if not tasks:
        return API.Output.fate_flow_exception(NoFoundTask())
    return API.Output.json(code=ReturnCode.Base.SUCCESS, message="success",
                           data=[task.to_human_model_dict() for task in tasks])


@manager.route('/task/list/query', methods=['GET'])
@API.Input.params(limit=fields.Integer(required=False))
@API.Input.params(page=fields.Integer(required=False))
@API.Input.params(job_id=fields.String(required=False))
@API.Input.params(role=fields.String(required=False))
@API.Input.params(party_id=fields.String(required=False))
@API.Input.params(task_name=fields.String(required=False))
@API.Input.params(order_by=fields.String(required=False))
@API.Input.params(order=fields.String(required=False))
def query_task_list(limit=0, page=0, job_id=None, role=None, party_id=None, task_name=None, order_by=None, order=None):
    count, data = JobController.query_task_list(
        limit, page, job_id, role, party_id, task_name, order_by, order
    )
    return API.Output.json(
        code=ReturnCode.Base.SUCCESS, message="success",
        data={"count": count, "data": data}
    )


@manager.route('/log/download', methods=['POST'])
@API.Input.json(job_id=fields.String(required=True))
def download_job_logs(job_id):
    job_log_dir = job_utils.get_job_log_directory(job_id=job_id)
    if not os.path.exists(job_log_dir):
        return API.Output.fate_flow_exception(e=FileNoFound(path=job_log_dir))
    memory_file = io.BytesIO()
    with tarfile.open(fileobj=memory_file, mode='w:gz') as tar:
        for root, _, files in os.walk(job_log_dir):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, job_log_dir)
                tar.add(full_path, rel_path)
    memory_file.seek(0)
    return API.Output.file(memory_file, attachment_filename=f'job_{job_id}_log.tar.gz', as_attachment=True)


@manager.route('/queue/clean', methods=['POST'])
def clean_queue():
    data = JobController.clean_queue()
    return API.Output.json(data=data)


@manager.route('/clean', methods=['POST'])
@API.Input.json(job_id=fields.String(required=True))
def clean_job(job_id):
    JobController.clean_job(job_id=job_id)
    return API.Output.json()


@manager.route('/dag/dependency', methods=['GET'])
@API.Input.json(job_id=fields.String(required=True))
@API.Input.json(role=fields.String(required=True))
@API.Input.json(party_id=fields.String(required=True))
def dag_dependency(job_id, role, party_id):
    jobs = JobController.query_job(job_id=job_id, role=role, party_id=party_id)
    if not jobs:
        return API.Output.fate_flow_exception(NoFoundJob(job_id=job_id))
    # todo
    return API.Output.json(data={})