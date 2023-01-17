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
from flask import request
from webargs import fields

from fate_flow.controller.task_controller import TaskController
from fate_flow.entity.types import ReturnCode
from fate_flow.manager.model_manager import PipelinedModel
from fate_flow.manager.output_manager import OutputDataTracking, OutputMetric
from fate_flow.operation.job_saver import JobSaver
from fate_flow.utils.api_utils import get_json_result, validate_request_json, validate_request_params

page_name = 'worker'


@manager.route('/task/status', methods=['POST'])
@validate_request_json(status=fields.String(required=True), execution_id=fields.String(required=True),
                       error=fields.String(required=False))
def report_task_status(status, execution_id, error=None):
    tasks = JobSaver.query_task(execution_id=execution_id)
    if tasks:
        task = tasks[0]
        task_info = {
            "party_status": status,
            "job_id": task.f_job_id,
            "role": task.f_role,
            "party_id": task.f_party_id,
            "task_id": task.f_task_id,
            "task_version": task.f_task_version
        }
        TaskController.update_task_status(task_info=task_info)
        if error:
            task_info.update({"error_report": error})
            TaskController.update_task(task_info)
        return get_json_result()
    return get_json_result(code=ReturnCode.TASK.NO_FOUND, message="no found task")


@manager.route('/task/status', methods=['GET'])
@validate_request_params(execution_id=fields.String(required=True))
def query_task_status(execution_id):
    tasks = JobSaver.query_task(execution_id=execution_id)
    if tasks:
        task_info = {
            "status": tasks[0].f_status,
        }
        return get_json_result(code=ReturnCode.TASK.SUCCESS, message="success", data=task_info)
    return get_json_result(code=ReturnCode.TASK.NO_FOUND, message="no found task")


@manager.route('/task/output/tracking', methods=['POST'])
@validate_request_json(execution_id=fields.String(required=True), meta_data=fields.Dict(required=True),
                       type=fields.String(required=True), uri=fields.String(required=True),
                       output_key=fields.String(required=True))
def log_output_artifacts(execution_id, meta_data, type, uri, output_key):
    tasks = JobSaver.query_task(execution_id=execution_id)
    if tasks:
        task = tasks[0]
        data_info = {
            "type": type,
            "uri": uri,
            "output_key": output_key,
            "meta": meta_data,
            "job_id": task.f_job_id,
            "role": task.f_role,
            "party_id": task.f_party_id,
            "task_id": task.f_task_id,
            "task_version": task.f_task_version,
            "task_name": task.f_task_name
        }
        OutputDataTracking.create(data_info)
        return get_json_result(code=ReturnCode.TASK.SUCCESS, message="success")
    return get_json_result(code=ReturnCode.TASK.NO_FOUND, message="no found task")


@manager.route('/task/model/<job_id>/<role>/<party_id>/<model_id>/<model_version>/<component>/<task_name>/<model_name>', methods=['POST'])
def save_output_model(job_id, role, party_id, model_id, model_version, component, task_name, model_name):
    file = request.files['file']
    PipelinedModel(job_id=job_id, model_id=model_id, model_version=model_version, role=role, party_id=party_id).save_output_model(
        task_name, model_name, component, model_file=file)
    return get_json_result()


@manager.route('/task/model/<job_id>/<role>/<party_id>/<model_id>/<model_version>/<component>/<task_name>/<model_name>', methods=['GET'])
def get_output_model(job_id, role, party_id, model_id, model_version, component, task_name, model_name):
    return PipelinedModel(
        model_id=model_id, model_version=model_version, job_id=job_id, role=role, party_id=party_id
    ).read_output_model(task_name, model_name)


@manager.route('/task/metric/<job_id>/<role>/<party_id>/<task_name>/<task_id>/<task_version>/<name>', methods=["POST"])
@validate_request_json(data=fields.Dict(required=True), incomplete=fields.Bool(required=True))
def save_metric(job_id, role, party_id, task_name, task_id, task_version, name, data, incomplete):
    OutputMetric(job_id=job_id, role=role, party_id=party_id, task_name=task_name, task_id=task_id,
                 task_version=task_version).save_output_metrics(data, incomplete)
    return get_json_result()
