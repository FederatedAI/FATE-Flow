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

from fate_flow.controller.task import TaskController
from fate_flow.entity.code import ReturnCode
from fate_flow.errors.server_error import NoFoundTask
from fate_flow.manager.outputs.data import DataManager, OutputDataTracking
from fate_flow.manager.outputs.model import PipelinedModel
from fate_flow.manager.outputs.metric import OutputMetric
from fate_flow.manager.operation.job_saver import JobSaver
from fate_flow.utils.api_utils import API

page_name = 'worker'


@manager.route('/task/status', methods=['POST'])
@API.Input.json(execution_id=fields.String(required=True))
@API.Input.json(status=fields.String(required=True))
@API.Input.json(error=fields.String(required=False))
@API.Output.runtime_exception(code=ReturnCode.API.COMPONENT_OUTPUT_EXCEPTION)
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


@manager.route('/model/save', methods=['POST'])
@API.Input.form(model_id=fields.String(required=True))
@API.Input.form(model_version=fields.String(required=True))
@API.Input.form(execution_id=fields.String(required=True))
@API.Input.form(output_key=fields.String(required=True))
@API.Input.form(type_name=fields.String(required=True))
@API.Output.runtime_exception(code=ReturnCode.API.COMPONENT_OUTPUT_EXCEPTION)
def upload_model(model_id, model_version, execution_id, output_key, type_name):
    task = JobSaver.query_task_by_execution_id(execution_id=execution_id)
    file = request.files['file']
    PipelinedModel.upload_model(
        model_file=file,
        job_id=task.f_job_id,
        task_name=task.f_task_name,
        role=task.f_role,
        party_id=task.f_party_id,
        output_key=output_key,
        model_id=model_id,
        model_version=model_version,
        type_name=type_name
    )
    return API.Output.json(code=ReturnCode.Base.SUCCESS, message="success")


@manager.route('/model/download', methods=['GET'])
@API.Input.params(model_id=fields.String(required=True))
@API.Input.params(model_version=fields.String(required=True))
@API.Input.params(role=fields.String(required=True))
@API.Input.params(party_id=fields.String(required=True))
@API.Input.params(task_name=fields.String(required=True))
@API.Input.params(output_key=fields.String(required=True))
@API.Output.runtime_exception(code=ReturnCode.API.COMPONENT_OUTPUT_EXCEPTION)
def download_model(model_id, model_version, role, party_id, task_name, output_key):
    return PipelinedModel.download_model(
        model_id=model_id,
        model_version=model_version,
        role=role,
        party_id=party_id,
        task_name=task_name,
        output_key=output_key
    )


@manager.route('/data/tracking/query', methods=['GET'])
@API.Input.params(job_id=fields.String(required=False))
@API.Input.params(role=fields.String(required=False))
@API.Input.params(party_id=fields.String(required=False))
@API.Input.params(task_name=fields.String(required=False))
@API.Input.params(output_key=fields.String(required=False))
@API.Input.params(namespace=fields.String(required=False))
@API.Input.params(name=fields.String(required=False))
@API.Output.runtime_exception(code=ReturnCode.API.COMPONENT_OUTPUT_EXCEPTION)
def query_data_tracking(job_id=None, role=None, party_id=None, task_name=None, output_key=None, namespace=None, name=None):
    tracking_list = []
    if not namespace and not name:
        data_info = {
            "job_id": job_id,
            "role": role,
            "party_id": party_id,
            "task_name": task_name,
            "output_key": output_key
        }
        tasks = JobSaver.query_task(job_id=job_id, role=role, party_id=party_id, task_name=task_name)
        if not tasks:
            return API.Output.fate_flow_exception(e=NoFoundTask(job_id=job_id, role=role, party_id=party_id,
                                                                task_name=task_name))
        data_info.update({
            "task_id": tasks[0].f_task_id,
            "task_version": tasks[0].f_task_version
        })

        data_list = OutputDataTracking.query(**data_info)
        if not data_list:
            return API.Output.json(code=ReturnCode.Task.NO_FOUND_MODEL_OUTPUT, message="failed")
        for data in data_list:
            info, _ = DataManager.get_data_info(data.f_namespace, data.f_name)
            tracking_list.append(info)
    else:
        info, _ = DataManager.get_data_info(namespace, name)
        tracking_list.append(info)
    return API.Output.json(code=ReturnCode.Base.SUCCESS, message="success", data=tracking_list)


@manager.route('/data/tracking/save', methods=['POST'])
@API.Input.json(execution_id=fields.String(required=True))
@API.Input.json(meta_data=fields.Dict(required=True))
@API.Input.json(uri=fields.String(required=True))
@API.Input.json(output_key=fields.String(required=True))
@API.Input.json(namespace=fields.String(required=True))
@API.Input.json(name=fields.String(required=True))
@API.Input.json(overview=fields.Dict(required=True))
@API.Input.json(partitions=fields.Int(required=False))
@API.Input.json(source=fields.Dict(required=True))
@API.Input.json(data_type=fields.String(required=True))
@API.Input.json(index=fields.Int(required=True))
@API.Output.runtime_exception(code=ReturnCode.API.COMPONENT_OUTPUT_EXCEPTION)
def save_data_tracking(execution_id, meta_data, uri, output_key, namespace, name, overview, source, data_type, index,
                       partitions=None):
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
        "name": name,
        "index": index
    }
    OutputDataTracking.create(data_info)
    if uri:
        DataManager.create_data_table(
            namespace=namespace, name=name, uri=uri, partitions=partitions,
            data_meta=meta_data, source=source, data_type=data_type,
            count=overview.get("count", None), part_of_data=overview.get("samples", [])
        )
    return API.Output.json(code=ReturnCode.Base.SUCCESS, message="success")


@manager.route('/metric/save', methods=["POST"])
@API.Input.json(execution_id=fields.String(required=True))
@API.Input.json(data=fields.List(fields.Dict()))
@API.Output.runtime_exception(code=ReturnCode.API.COMPONENT_OUTPUT_EXCEPTION)
def save_metric(execution_id, data):
    task = JobSaver.query_task_by_execution_id(execution_id=execution_id)
    OutputMetric(job_id=task.f_job_id, role=task.f_role, party_id=task.f_party_id, task_name=task.f_task_name,
                 task_id=task.f_task_id, task_version=task.f_task_version).save_output_metrics(data)
    return API.Output.json()


@manager.route('/metric/save/<execution_id>', methods=["POST"])
@API.Input.json(data=fields.List(fields.Dict()))
@API.Output.runtime_exception(code=ReturnCode.API.COMPONENT_OUTPUT_EXCEPTION)
def save_metrics(execution_id, data):
    task = JobSaver.query_task_by_execution_id(execution_id=execution_id)
    OutputMetric(job_id=task.f_job_id, role=task.f_role, party_id=task.f_party_id, task_name=task.f_task_name,
                 task_id=task.f_task_id, task_version=task.f_task_version).save_output_metrics(data)
    return API.Output.json()
