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
from flask import request

from fate_flow.utils import job_utils
from fate_flow.utils.api_utils import get_json_result, error_response
from fate_arch.common import file_utils


@manager.route('/job_config/get', methods=['POST'])
def get_config():
    kwargs = {}
    job_configuration = None

    for i in ('job_id', 'role', 'party_id'):
        if request.json.get(i) is None:
            return error_response(400, f"'{i}' is required.")
        kwargs[i] = str(request.json[i])

    for i in ('component_name', 'task_id', 'task_version'):
        if request.json.get(i) is None:
            break
        kwargs[i] = str(request.json[i])
    else:
        try:
            job_configuration = job_utils.get_task_using_job_conf(**kwargs)
        except Exception:
            pass

    if job_configuration is None:
        job_configuration = job_utils.get_job_configuration(kwargs['job_id'], kwargs['role'], kwargs['party_id'])

    if job_configuration is None:
        return error_response(404, 'Job not found.')

    return get_json_result(data=job_configuration.to_dict())


@manager.route('/json_conf/load', methods=['POST'])
def load_json_conf():
    job_conf = file_utils.load_json_conf(request.json.get("config_path"))
    return get_json_result(data=job_conf)
