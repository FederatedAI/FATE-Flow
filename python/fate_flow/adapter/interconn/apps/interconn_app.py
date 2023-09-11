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

from fate_flow.utils.api_utils import API

page_name = 'interconn'


@manager.route('/schedule/job/create_all', methods=['POST'])
@API.Input.json(flow_id=fields.String(required=False))
@API.Input.json(job_id=fields.String(required=True))
@API.Input.json(dag=fields.Dict(required=True))
@API.Input.json(config=fields.Dict(required=True))
@API.Input.json(old_job_id=fields.String(required=False))
def create_job_all(job_id, dag, config, flow_id=None, old_job_id=None):
    return API.Output.json()


@manager.route('/schedule/job/create', methods=['POST'])
@API.Input.json(flow_id=fields.String(required=False))
@API.Input.json(job_id=fields.String(required=True))
@API.Input.json(dag=fields.Dict(required=True))
@API.Input.json(config=fields.Dict(required=True))
@API.Input.json(old_job_id=fields.String(required=False))
def create_job(job_id, dag, config, flow_id=None, old_job_id=None):
    return API.Output.json()


@manager.route('/schedule/job/start', methods=['POST'])
@API.Input.json(job_id=fields.String(required=True))
def start_job():
    return API.Output.json()


@manager.route('/schedule/task/start', methods=['POST'])
@API.Input.json(job_id=fields.String(required=True))
@API.Input.json(task_id=fields.String(required=True))
@API.Input.json(task_name=fields.String(required=True))
def start_task(job_id, task_id, task_name):
    return API.Output.json()


@manager.route('/schedule/job/stop_all', methods=['POST'])
@API.Input.json(job_id=fields.String(required=True))
@API.Input.json(task_name=fields.String(required=False))
def stop_job_all(job_id, task_name=None):
    return API.Output.json()


@manager.route('/schedule/job/stop', methods=['POST'])
@API.Input.json(job_id=fields.String(required=True))
@API.Input.json(task_name=fields.String(required=False))
def stop_job(job_id, task_name=None):
    return API.Output.json()


@manager.route('/schedule/job/status_all', methods=['GET'])
@API.Input.params(job_id=fields.String(required=True))
def get_job_status_all(job_id):
    return API.Output.json(job_status="", status=[])


@manager.route('/schedule/job/audit_confirm', methods=['POST'])
@API.Input.json(job_id=fields.String(required=True))
@API.Input.json(status=fields.String(required=True))
def audit_confirm(job_id, status):
    return API.Output.json()


@manager.route('/schedule/task/poll', methods=['POST'])
@API.Input.json(task_id=fields.String(required=True))
@API.Input.json(role=fields.String(required=True))
def poll_task(task_id, role):
    return API.Output.json(status="")


@manager.route('/schedule/task/callback', methods=['POST'])
@API.Input.json(task_id=fields.String(required=True))
@API.Input.json(role=fields.String(required=True))
@API.Input.json(status=fields.String(required=True))
def callback_task(task_id, role, status):
    return API.Output.json()
