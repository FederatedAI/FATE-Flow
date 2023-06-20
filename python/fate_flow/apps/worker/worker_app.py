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
from fate_flow.manager.data.data_manager import DataManager
from fate_flow.manager.model.model_manager import PipelinedModel
from fate_flow.manager.metric.metric_manager import OutputMetric
from fate_flow.manager.service.output_manager import OutputDataTracking
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


@manager.route('/model/save', methods=['POST'])
@API.Input.json(model_id=fields.String(required=True))
@API.Input.json(model_version=fields.String(required=True))
@API.Input.json(execution_id=fields.String(required=True))
@API.Input.json(meta_data=fields.Dict(required=True))
@API.Input.json(output_key=fields.String(required=True))
def upload_model(model_id, model_version, execution_id, meta_data, output_key):
    task = JobSaver.query_task_by_execution_id(execution_id=execution_id)
    file = request.files['file']
    PipelinedModel.upload_model(
        model_file=file,
        job_id=task.f_job_id,
        task_name=task.f_task_name,
        output_key=output_key,
        model_id=model_id,
        model_version=model_version,
        meta_data=meta_data
    )
    return API.Output.json(code=ReturnCode.Base.SUCCESS, message="success")


@manager.route('/model/download', methods=['GET'])
@API.Input.params(model_id=fields.String(required=True))
@API.Input.params(model_version=fields.String(required=True))
@API.Input.params(role=fields.String(required=True))
@API.Input.params(party_id=fields.String(required=True))
@API.Input.params(task_name=fields.String(required=True))
@API.Input.params(output_key=fields.String(required=True))
def download_model(model_id, model_version, role, party_id, task_name, output_key):
    return PipelinedModel.download_model(model_id, model_version, role, party_id, task_name, output_key)


@manager.route('/data/tracking/query', methods=['GET'])
@API.Input.params(job_id=fields.String(required=False))
@API.Input.params(role=fields.String(required=False))
@API.Input.params(party_id=fields.String(required=False))
@API.Input.params(task_name=fields.String(required=False))
@API.Input.params(output_key=fields.String(required=False))
@API.Input.params(namespace=fields.String(required=False))
@API.Input.params(name=fields.String(required=False))
def query_data_tracking(job_id=None, role=None, party_id=None, task_name=None, output_key=None, namespace=None, name=None):
    if not namespace and name:
        data_info = {
            "job_id": job_id,
            "role": role,
            "party_id": party_id,
            "task_name": task_name,
            "output_key": output_key
        }
        data_list = OutputDataTracking.query(data_info)
        if data_list:
            data = data_list[0]
            namespace, name = data.f_namespace, data.f_name
        else:
            return API.Output.json(code=ReturnCode.Base.SUCCESS, message="success")
    info = DataManager.get_data_info(namespace, name)
    return API.Output.json(code=ReturnCode.Base.SUCCESS, message="success", data=info)



@manager.route('/data/tracking/save', methods=['POST'])
@API.Input.json(execution_id=fields.String(required=True))
@API.Input.json(meta_data=fields.Dict(required=True))
@API.Input.json(uri=fields.String(required=True))
@API.Input.json(output_key=fields.String(required=True))
@API.Input.params(namespace=fields.String(required=True))
@API.Input.params(name=fields.String(required=True))
@API.Input.params(partitions=fields.String(required=True))
def save_data_tracking(execution_id, meta_data, uri, output_key, namespace, name, partitions):
    task = JobSaver.query_task_by_execution_id(execution_id=execution_id)
    data_info = {
        "uri": uri,
        "output_key": output_key,
        "job_id": task.f_job_id,
        "role": task.f_role,
        "party_id": task.f_party_id,
        "task_id": task.f_task_id,
        "task_version": task.f_task_version,
        "task_name": task.f_task_name,
        "namespace": namespace,
        "name": name
    }
    OutputDataTracking.create(data_info)
    DataManager.create_data_table(
        namespace=namespace, name=name, uri=uri, partitions=partitions,
        data_meta=meta_data, origin=f"{task.f_job_id}.{task.f_task_name}"
    )
    return API.Output.json(code=ReturnCode.Base.SUCCESS, message="success")


@manager.route('/metric/save', methods=["POST"])
@API.Input.json(execution_id=fields.String(required=True))
@API.Input.json(data=fields.Dict(required=True))
@API.Input.json(incomplete=fields.Bool(required=True))
def save_metric(execution_id, data, incomplete):
    task = JobSaver.query_task_by_execution_id(execution_id=execution_id)
    OutputMetric(job_id=task.f_job_id, role=task.f_role, party_id=task.f_party_id, task_name=task.f_task_name,
                 task_id=task.f_task_id, task_version=task.f_task_version).save_output_metrics(data, incomplete)
    return API.Output.json()
