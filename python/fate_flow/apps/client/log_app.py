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

from fate_flow.manager.log.log_manager import LogManager
from fate_flow.utils.api_utils import API


@manager.route('/count', methods=['GET'])
@API.Input.json(log_type=fields.String(required=True))
@API.Input.json(job_id=fields.String(required=True))
@API.Input.json(role=fields.String(required=False))
@API.Input.json(party_id=fields.String(required=False))
@API.Input.json(task_name=fields.String(required=False))
def count(log_type, job_id, role=None, party_id=None, task_name=None):
    data = LogManager(log_type, job_id, role=role, party_id=party_id, task_name=task_name).count()
    return API.Output.json(data=data)


@manager.route('/query', methods=['GET'])
@API.Input.json(log_type=fields.String(required=True))
@API.Input.json(job_id=fields.String(required=True))
@API.Input.json(role=fields.String(required=False))
@API.Input.json(party_id=fields.String(required=False))
@API.Input.json(task_name=fields.String(required=False))
@API.Input.json(begin=fields.Integer(required=False))
@API.Input.json(end=fields.Integer(required=False))
def get(log_type, job_id, begin, end, role=None, party_id=None, task_name=None):
    data = LogManager(log_type, job_id, role=role, party_id=party_id, task_name=task_name).cat_log(begin=begin, end=end)
    return API.Output.json(data=data)
