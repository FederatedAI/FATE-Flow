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
import io
import json
import os
import tarfile

from flask import abort, request, send_file

from fate_arch.common.base_utils import json_dumps, json_loads
from fate_flow.controller.job_controller import JobController
from fate_flow.entity import JobConfigurationBase, RetCode, RunParameters
from fate_flow.entity.run_status import FederatedSchedulingStatusCode, JobStatus
from fate_flow.operation.job_clean import JobClean
from fate_flow.operation.job_saver import JobSaver
from fate_flow.operation.job_tracker import Tracker
from fate_flow.scheduler.dag_scheduler import DAGScheduler
from fate_flow.scheduler.federated_scheduler import FederatedScheduler
from fate_flow.settings import TEMP_DIRECTORY, stat_logger, PARTY_ID
from fate_flow.utils import job_utils, log_utils, schedule_utils, api_utils
from fate_flow.utils.api_utils import error_response, get_json_result
from fate_flow.utils.config_adapter import JobRuntimeConfigAdapter
from fate_flow.utils.log_utils import schedule_logger


@manager.route('/submit', methods=['POST'])
def submit_job():
    submit_result = JobController.request_create_job(JobConfigurationBase(**request.json))
    return get_json_result(**submit_result)


@manager.route('/stop', methods=['POST'])
def stop_job():
    job_id = request.json.get('job_id')
    stop_status = request.json.get("stop_status", "canceled")
    jobs = JobSaver.query_job(job_id=job_id)
    if jobs:
        schedule_logger(job_id).info(f"stop job on this party")
        kill_status, kill_details = JobController.stop_jobs(job_id=job_id, stop_status=stop_status)
        schedule_logger(job_id).info(f"stop job on this party status {kill_status}")
        schedule_logger(job_id).info(f"request stop job to {stop_status}")
        status_code, response = FederatedScheduler.request_stop_job(party_id=jobs[0].f_scheduler_party_id,
                                                                    job_id=job_id, stop_status=stop_status)
        if status_code == FederatedSchedulingStatusCode.SUCCESS:
            return get_json_result(retcode=RetCode.SUCCESS, retmsg=f"stop job on this party {'success' if kill_status else 'failed'}; stop job on all party success")
        else:
            return get_json_result(retcode=RetCode.OPERATING_ERROR, retmsg=f"stop job on this party {kill_status}", data=response)
    else:
        schedule_logger(job_id).info(f"can not found job to stop")
        return get_json_result(retcode=RetCode.DATA_ERROR, retmsg="can not found job")


@manager.route('/rerun', methods=['POST'])
def rerun_job():
    job_id = request.json.get("job_id")
    jobs = JobSaver.query_job(job_id=job_id)
    if jobs:
        status_code, response = FederatedScheduler.request_rerun_job(job=jobs[0], command_body=request.json)
        if status_code == FederatedSchedulingStatusCode.SUCCESS:
            return get_json_result(retcode=RetCode.SUCCESS, retmsg="rerun job success")
        else:
            return get_json_result(retcode=RetCode.OPERATING_ERROR, retmsg="rerun job failed:\n{}".format(json_dumps(response)))
    else:
        return get_json_result(retcode=RetCode.DATA_ERROR, retmsg="can not found job")


@manager.route('/query', methods=['POST'])
def query_job():
    jobs = JobSaver.query_job(**request.json)
    if not jobs:
        return get_json_result(retcode=0, retmsg='no job could be found', data=[])
    return get_json_result(retcode=0, retmsg='success', data=[job.to_dict() for job in jobs])


@manager.route('/task/query', methods=['POST'])
def query_task():
    tasks = JobSaver.query_task(**request.json)
    if not tasks:
        return get_json_result(retcode=101, retmsg='find task failed')
    return get_json_result(retcode=0, retmsg='success', data=[task.to_dict() for task in tasks])
