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

from fate_flow.apps.desc import LOG_TYPE, JOB_ID, ROLE, PARTY_ID, TASK_NAME, INSTANCE_ID, BEGIN, END
from fate_flow.manager.outputs.log import LogManager
from fate_flow.utils.api_utils import API
from fate_flow.utils.wraps_utils import cluster_route


@manager.route('/count', methods=['GET'])
@API.Input.params(log_type=fields.String(required=True), desc=LOG_TYPE)
@API.Input.params(job_id=fields.String(required=True), desc=JOB_ID)
@API.Input.params(role=fields.String(required=False), desc=ROLE)
@API.Input.params(party_id=fields.String(required=False), desc=PARTY_ID)
@API.Input.params(task_name=fields.String(required=False), desc=TASK_NAME)
@API.Input.params(instance_id=fields.String(required=False), desc=INSTANCE_ID)
@cluster_route
def count(log_type, job_id, role=None, party_id=None, task_name=None, instance_id=None):
    data = LogManager(log_type, job_id, role=role, party_id=party_id, task_name=task_name).count()
    return API.Output.json(data=data)


@manager.route('/query', methods=['GET'])
@API.Input.params(log_type=fields.String(required=True), desc=LOG_TYPE)
@API.Input.params(job_id=fields.String(required=True), desc=JOB_ID)
@API.Input.params(role=fields.String(required=True), desc=ROLE)
@API.Input.params(party_id=fields.String(required=True), desc=PARTY_ID)
@API.Input.params(task_name=fields.String(required=False), desc=TASK_NAME)
@API.Input.params(begin=fields.Integer(required=False), desc=BEGIN)
@API.Input.params(end=fields.Integer(required=False), desc=END)
@API.Input.params(instance_id=fields.String(required=False), desc=INSTANCE_ID)
@cluster_route
def get(log_type, job_id, role, party_id, task_name=None, begin=None, end=None, instance_id=None):
    data = LogManager(log_type, job_id, role=role, party_id=party_id, task_name=task_name).cat_log(begin=begin, end=end)
    return API.Output.json(data=data)
