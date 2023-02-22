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

from fate_flow.entity.types import ReturnCode
from fate_flow.manager.model_manager import PipelinedModel
from fate_flow.manager.output_manager import OutputMetric
from fate_flow.operation.job_saver import JobSaver
from fate_flow.utils.api_utils import get_json_result, validate_request_params


@manager.route('/metric/key/query', methods=['GET'])
@validate_request_params(job_id=fields.String(required=True), role=fields.String(required=True),
                         party_id=fields.String(required=True), task_name=fields.String(required=True))
def query_metric_key(job_id, role, party_id, task_name):
    tasks = JobSaver.query_task(job_id=job_id, role=role, party_id=party_id, task_name=task_name)
    if not tasks:
        return get_json_result(code=ReturnCode.Task.NOT_FOUND, message="task not found")
    metric_keys = OutputMetric(job_id=job_id, role=role, party_id=party_id, task_name=task_name,
                               task_id=tasks[0].f_task_id, task_version=tasks[0].f_task_version).query_metric_keys()
    return get_json_result(code=ReturnCode.Base.SUCCESS, message='success', data=metric_keys)


@manager.route('/metric/query', methods=['GET'])
@validate_request_params(job_id=fields.String(required=True), role=fields.String(required=True),
                         party_id=fields.String(required=True), task_name=fields.String(required=True),
                         filters=fields.Dict(required=False))
def query_metric(job_id, role, party_id, task_name, filters=None):
    tasks = JobSaver.query_task(job_id=job_id, role=role, party_id=party_id, task_name=task_name)
    if not tasks:
        return get_json_result(code=ReturnCode.Task.NOT_FOUND, message="task not found")
    metrics = OutputMetric(job_id=job_id, role=role, party_id=party_id, task_name=task_name, task_id=tasks[0].f_task_id,
                           task_version=tasks[0].f_task_version).read_metrics(filters)
    return get_json_result(code=ReturnCode.Base.SUCCESS, message='success', data=metrics)


@manager.route('/model/query', methods=['GET'])
@validate_request_params(job_id=fields.String(required=True), role=fields.String(required=True),
                         party_id=fields.String(required=True), task_name=fields.String(required=True))
def query_model(job_id, role, party_id, task_name):
    tasks = JobSaver.query_task(job_id=job_id, role=role, party_id=party_id, task_name=task_name)
    if not tasks:
        return get_json_result(code=ReturnCode.Task.NOT_FOUND, message="task not found")

    model_data, message = PipelinedModel(role=role, party_id=party_id, job_id=job_id).read_model_data(task_name)
    return get_json_result(code=ReturnCode.Base.SUCCESS, message=message, data=model_data)
