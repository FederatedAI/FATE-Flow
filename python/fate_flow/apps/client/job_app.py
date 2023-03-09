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
from fate_flow.entity.code import ReturnCode
from fate_flow.utils.api_utils import API


@manager.route('/submit', methods=['POST'])
@API.Input.json(dag_schema=fields.Dict(required=True))
def submit_job(dag_schema):
    submit_result = JobController.request_create_job(dag_schema)
    return API.Output.json(**submit_result)


@manager.route('/query', methods=['GET'])
@API.Input.params(job_id=fields.String(required=False))
@API.Input.params(role=fields.String(required=False))
@API.Input.params(party_id=fields.String(required=False))
@API.Input.params(status=fields.String(required=False))
def query_job(job_id=None, role=None, party_id=None, status=None):
    jobs = JobController.query_job(job_id=job_id, role=role, party_id=party_id, status=status)
    if not jobs:
        return API.Output.json(code=ReturnCode.Job.NOT_FOUND, message="job no found")
    return API.Output.json(code=ReturnCode.Base.SUCCESS, message="success",
                           data=[job.to_human_model_dict() for job in jobs])


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
        return API.Output.json(code=ReturnCode.Task.NOT_FOUND, message="task no found")
    return API.Output.json(code=ReturnCode.Base.SUCCESS, message="success",
                           data=[task.to_human_model_dict() for task in tasks])


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
        return API.Output.json(code=ReturnCode.Job.NOT_FOUND, message="job not found")
    rerun_result = JobController.request_rerun_job(job=jobs[0])
    return API.Output.json(**rerun_result)
