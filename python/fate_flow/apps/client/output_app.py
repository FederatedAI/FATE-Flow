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

from fate_flow.apps.desc import JOB_ID, ROLE, PARTY_ID, TASK_NAME, FILTERS, OUTPUT_KEY
from fate_flow.entity.code import ReturnCode
from fate_flow.entity.types import PROTOCOL
from fate_flow.errors.server_error import NoFoundTask
from fate_flow.manager.outputs.data import DataManager
from fate_flow.manager.outputs.model import PipelinedModel
from fate_flow.manager.outputs.metric import OutputMetric
from fate_flow.manager.operation.job_saver import JobSaver
from fate_flow.utils.api_utils import API


@manager.route('/metric/key/query', methods=['GET'])
@API.Input.params(job_id=fields.String(required=True), desc=JOB_ID)
@API.Input.params(role=fields.String(required=True), desc=ROLE)
@API.Input.params(party_id=fields.String(required=True), desc=PARTY_ID)
@API.Input.params(task_name=fields.String(required=True), desc=TASK_NAME)
def query_metric_key(job_id, role, party_id, task_name):
    tasks = JobSaver.query_task(job_id=job_id, role=role, party_id=party_id, task_name=task_name)
    if not tasks:
        return API.Output.fate_flow_exception(e=NoFoundTask(job_id=job_id, role=role, party_id=party_id,
                                                            task_name=task_name))
    metric_keys = OutputMetric(job_id=job_id, role=role, party_id=party_id, task_name=task_name,
                               task_id=tasks[0].f_task_id, task_version=tasks[0].f_task_version).query_metric_keys()
    return API.Output.json(code=ReturnCode.Base.SUCCESS, message='success', data=metric_keys)


@manager.route('/metric/query', methods=['GET'])
@API.Input.params(job_id=fields.String(required=True), desc=PARTY_ID)
@API.Input.params(role=fields.String(required=True), desc=ROLE)
@API.Input.params(party_id=fields.String(required=True), desc=PARTY_ID)
@API.Input.params(task_name=fields.String(required=True), desc=TASK_NAME)
@API.Input.params(filters=fields.Dict(required=False), desc=FILTERS)
def query_metric(job_id, role, party_id, task_name, filters=None):
    tasks = JobSaver.query_task(job_id=job_id, role=role, party_id=party_id, task_name=task_name, ignore_protocol=True)
    if not tasks:
        return API.Output.fate_flow_exception(
            e=NoFoundTask(job_id=job_id, role=role, party_id=party_id, task_name=task_name)
        )

    kind = tasks[0].f_protocol
    if kind != PROTOCOL.FATE_FLOW:
        from fate_flow.adapter import AdapterJobController
        metrics = AdapterJobController(kind).query_output_metric()
    else:
        metrics = OutputMetric(
            job_id=job_id,
            role=role,
            party_id=party_id,
            task_name=task_name,
            task_id=tasks[0].f_task_id,
            task_version=tasks[0].f_task_version
        ).read_metrics(filters)
    return API.Output.json(code=ReturnCode.Base.SUCCESS, message='success', data=metrics)


@manager.route('/metric/delete', methods=['POST'])
@API.Input.json(job_id=fields.String(required=True), desc=JOB_ID)
@API.Input.json(role=fields.String(required=True), desc=ROLE)
@API.Input.json(party_id=fields.String(required=True), desc=PARTY_ID)
@API.Input.json(task_name=fields.String(required=True), desc=TASK_NAME)
def delete_metric(job_id, role, party_id, task_name):
    tasks = JobSaver.query_task(job_id=job_id, role=role, party_id=party_id, task_name=task_name)
    if not tasks:
        return API.Output.fate_flow_exception(e=NoFoundTask(job_id=job_id, role=role, party_id=party_id,
                                                            task_name=task_name))
    metric_keys = OutputMetric(
        job_id=job_id, role=role, party_id=party_id, task_name=task_name,
        task_id=tasks[0].f_task_id, task_version=tasks[0].f_task_version
    ).delete_metrics()
    return API.Output.json(code=ReturnCode.Base.SUCCESS, message='success', data=metric_keys)


@manager.route('/model/query', methods=['GET'])
@API.Input.params(job_id=fields.String(required=True), desc=JOB_ID)
@API.Input.params(role=fields.String(required=True), desc=ROLE)
@API.Input.params(party_id=fields.String(required=True), desc=PARTY_ID)
@API.Input.params(task_name=fields.String(required=True), desc=TASK_NAME)
def query_model(job_id, role, party_id, task_name):
    tasks = JobSaver.query_task(job_id=job_id, role=role, party_id=party_id, task_name=task_name, ignore_protocol=True)
    if not tasks:
        return API.Output.fate_flow_exception(e=NoFoundTask(job_id=job_id, role=role, party_id=party_id,
                                                            task_name=task_name))
    task = tasks[0]

    kind = task.f_protocol
    if kind != PROTOCOL.FATE_FLOW:
        from fate_flow.adapter import AdapterJobController
        model_data = AdapterJobController(kind).query_output_model()
    else:
        model_data = PipelinedModel.read_model(task.f_job_id, task.f_role, task.f_party_id, task.f_task_name)
    return API.Output.json(data=model_data)


@manager.route('/model/download', methods=['GET'])
@API.Input.params(job_id=fields.String(required=True), desc=JOB_ID)
@API.Input.params(role=fields.String(required=True), desc=ROLE)
@API.Input.params(party_id=fields.String(required=True), desc=PARTY_ID)
@API.Input.params(task_name=fields.String(required=True), desc=TASK_NAME)
def download(job_id, role, party_id, task_name):
    tasks = JobSaver.query_task(job_id=job_id, role=role, party_id=party_id, task_name=task_name)
    if not tasks:
        return API.Output.fate_flow_exception(e=NoFoundTask(job_id=job_id, role=role, party_id=party_id,
                                                            task_name=task_name))
    task = tasks[0]
    return PipelinedModel.download_model(job_id=task.f_job_id, role=task.f_role, party_id=task.f_party_id,
                                         task_name=task.f_task_name)


@manager.route('/model/delete', methods=['POST'])
@API.Input.json(job_id=fields.String(required=True), desc=JOB_ID)
@API.Input.json(role=fields.String(required=True), desc=ROLE)
@API.Input.json(party_id=fields.String(required=True), desc=PARTY_ID)
@API.Input.json(task_name=fields.String(required=True), desc=TASK_NAME)
def delete_model(job_id, role, party_id, task_name):
    tasks = JobSaver.query_task(job_id=job_id, role=role, party_id=party_id, task_name=task_name)
    if not tasks:
        return API.Output.fate_flow_exception(e=NoFoundTask(job_id=job_id, role=role, party_id=party_id,
                                                            task_name=task_name))
    task = tasks[0]
    PipelinedModel.delete_model(
        job_id=task.f_job_id,
        role=task.f_role,
        party_id=task.f_party_id,
        task_name=task.f_task_name)
    return API.Output.json()


@manager.route('/data/download', methods=['GET'])
@API.Input.params(job_id=fields.String(required=True), desc=JOB_ID)
@API.Input.params(role=fields.String(required=True), desc=ROLE)
@API.Input.params(party_id=fields.String(required=True), desc=PARTY_ID)
@API.Input.params(task_name=fields.String(required=True), desc=TASK_NAME)
@API.Input.params(output_key=fields.String(required=False), desc=OUTPUT_KEY)
def output_data_download(job_id, role, party_id, task_name, output_key=None):
    tasks = JobSaver.query_task(job_id=job_id, role=role, party_id=party_id, task_name=task_name)
    if not tasks:
        return API.Output.fate_flow_exception(e=NoFoundTask(job_id=job_id, role=role, party_id=party_id,
                                                            task_name=task_name))
    task = tasks[0]
    return DataManager.download_output_data(
        job_id=task.f_job_id,
        role=task.f_role,
        party_id=task.f_party_id,
        task_name=task.f_task_name,
        task_id=task.f_task_id,
        task_version=task.f_task_version,
        output_key=output_key,
        tar_file_name=f"{job_id}_{role}_{party_id}_{task_name}"

    )


@manager.route('/data/table', methods=['GET'])
@API.Input.params(job_id=fields.String(required=True), desc=JOB_ID)
@API.Input.params(role=fields.String(required=True), desc=ROLE)
@API.Input.params(party_id=fields.String(required=True), desc=PARTY_ID)
@API.Input.params(task_name=fields.String(required=True), desc=TASK_NAME)
def output_data_table(job_id, role, party_id, task_name):
    tasks = JobSaver.query_task(job_id=job_id, role=role, party_id=party_id, task_name=task_name)
    if not tasks:
        return API.Output.fate_flow_exception(e=NoFoundTask(job_id=job_id, role=role, party_id=party_id,
                                                            task_name=task_name))
    task = tasks[0]
    return DataManager.query_output_data_table(
        job_id=task.f_job_id,
        role=task.f_role,
        party_id=task.f_party_id,
        task_name=task.f_task_name,
        task_id=task.f_task_id,
        task_version=task.f_task_version
    )


@manager.route('/data/display', methods=['GET'])
@API.Input.params(job_id=fields.String(required=True), desc=JOB_ID)
@API.Input.params(role=fields.String(required=True), desc=ROLE)
@API.Input.params(party_id=fields.String(required=True), desc=PARTY_ID)
@API.Input.params(task_name=fields.String(required=True), desc=TASK_NAME)
def output_data_display(job_id, role, party_id, task_name):
    tasks = JobSaver.query_task(job_id=job_id, role=role, party_id=party_id, task_name=task_name)
    if not tasks:
        return API.Output.fate_flow_exception(e=NoFoundTask(job_id=job_id, role=role, party_id=party_id,
                                                            task_name=task_name))
    task = tasks[0]
    return DataManager.display_output_data(
        job_id=task.f_job_id,
        role=task.f_role,
        party_id=task.f_party_id,
        task_name=task.f_task_name,
        task_id=task.f_task_id,
        task_version=task.f_task_version
    )
