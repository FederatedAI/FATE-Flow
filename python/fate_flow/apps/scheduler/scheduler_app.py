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
from webargs import fields

from fate_flow.entity.spec.dag import DAGSchema
from fate_flow.errors.server_error import UpdateTaskFailed
from fate_flow.manager.operation.job_saver import ScheduleJobSaver
from fate_flow.scheduler.scheduler import DAGScheduler
from fate_flow.utils.api_utils import API

page_name = 'scheduler'


@manager.route('/job/create', methods=['POST'])
@API.Input.json(dag=fields.Dict(required=True))
@API.Input.json(schema_version=fields.String(required=True))
def create_job(dag, schema_version):
    dag = DAGSchema(dag=dag, schema_version=schema_version)
    submit_result = DAGScheduler.create_all_job(dag.dict())
    return API.Output.json(**submit_result)


@manager.route('/task/report', methods=['POST'])
@API.Input.json(job_id=fields.String(required=True))
@API.Input.json(role=fields.String(required=True))
@API.Input.json(party_id=fields.String(required=True))
@API.Input.json(task_id=fields.String(required=True))
@API.Input.json(task_version=fields.Integer(required=True))
@API.Input.json(status=fields.String(required=False))
def report_task(job_id, role, party_id, task_id, task_version, status=None):
    status = ScheduleJobSaver.update_task_status(task_info={
        "job_id": job_id,
        "role": role,
        "party_id": party_id,
        "task_id": task_id,
        "task_version": task_version,
        "status": status
    })
    if status:
        return API.Output.json()
    return API.Output.fate_flow_exception(UpdateTaskFailed(
        job_id=job_id, role=role, party_id=party_id,
        task_id=task_id, task_version=task_version, status=status)
    )


@manager.route('/job/stop', methods=['POST'])
@API.Input.json(job_id=fields.String(required=True))
@API.Input.json(stop_status=fields.String(required=False))
def stop_job(job_id, stop_status=None):
    retcode, retmsg = DAGScheduler.stop_job(job_id, stop_status)
    return API.Output.json(code=retcode, message=retmsg)


@manager.route('/job/rerun', methods=['POST'])
@API.Input.json(job_id=fields.String(required=True))
def rerun_job(job_id):
    DAGScheduler.rerun_job(job_id=job_id, auto=False)
    return API.Output.json()
