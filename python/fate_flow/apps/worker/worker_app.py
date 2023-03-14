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
from fate_flow.entity.code import ReturnCode
from fate_flow.manager.model.model_manager import PipelinedModel
from fate_flow.manager.service.output_manager import OutputDataTracking, OutputMetric
from fate_flow.operation.job_saver import JobSaver
from fate_flow.utils.api_utils import API

page_name = 'worker'


@manager.route('/task/status', methods=['POST'])
@API.Input.json(execution_id=fields.String(required=True))
@API.Input.json(status=fields.String(required=True))
@API.Input.json(error=fields.String(required=False))
def report_task_status(status, execution_id, error=None):
    task = JobSaver.query_task_by_execution_id(execution_id=execution_id)
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
    return API.Output.json()


@manager.route('/task/status', methods=['GET'])
@API.Input.params(execution_id=fields.String(required=True))
def query_task_status(execution_id):
    task = JobSaver.query_task_by_execution_id(execution_id=execution_id)

    task_info = {
        "status": task.f_status,
    }
    return API.Output.json(code=ReturnCode.Base.SUCCESS, message="success", data=task_info)


@manager.route('/task/output/tracking', methods=['POST'])
@API.Input.json(execution_id=fields.String(required=True))
@API.Input.json(meta_data=fields.Dict(required=True))
@API.Input.json(type=fields.String(required=True))
@API.Input.json(uri=fields.String(required=True))
@API.Input.json(output_key=fields.String(required=True))
def log_output_artifacts(execution_id, meta_data, type, uri, output_key):
    task = JobSaver.query_task_by_execution_id(execution_id=execution_id)
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
    return API.Output.json(code=ReturnCode.Base.SUCCESS, message="success")


@manager.route('/task/model/<model_id>/<model_version>/<dir_name>/<file_name>', methods=['POST'])
def upload_output_model(model_id, model_version, dir_name, file_name):
    file = request.files['file']
    PipelinedModel.upload_model(
        model_file=file,
        dir_name=dir_name,
        file_name=file_name,
        model_id=model_id,
        model_version=model_version
    )
    return API.Output.json()


@manager.route('/task/model/<model_id>/<model_version>/<dir_name>/<file_name>', methods=['GET'])
def download_output_model(model_id, model_version, dir_name, file_name):
    return PipelinedModel.download_model(model_id, model_version, dir_name, file_name)


@manager.route('/task/metric/<job_id>/<role>/<party_id>/<task_name>/<task_id>/<task_version>/<name>', methods=["POST"])
@API.Input.json(data=fields.Dict(required=True))
@API.Input.json(incomplete=fields.Bool(required=True))
def save_metric(job_id, role, party_id, task_name, task_id, task_version, name, data, incomplete):
    OutputMetric(job_id=job_id, role=role, party_id=party_id, task_name=task_name, task_id=task_id,
                 task_version=task_version).save_output_metrics(data, incomplete)
    return API.Output.json()
