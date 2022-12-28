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
from functools import wraps

from fate_flow.entity import RetCode
from fate_flow.entity.run_status import FederatedSchedulingStatusCode
from fate_flow.entity.types import Code
from fate_flow.operation.job_saver import ScheduleJobSaver
from fate_flow.runtime.runtime_config import RuntimeConfig
from fate_flow.utils.log_utils import schedule_logger


def get_tasks_by_task_id(task_id):
    return [{"job_id": task.f_job_id, "role": task.f_role, "party_id": task.f_party_id,
             "component": task.f_component, "task_id": task.f_task_id,
             "task_version": task.f_task_version} for task in
            ScheduleJobSaver.query_task(task_id=task_id, only_latest=True)]


def schedule_job(func):
    @wraps(func)
    def _inner(*args, **kwargs):
        _return = func(*args, **kwargs)
        schedule_logger(kwargs.get("job_id")).info(f"job command '{func.__name__}' return: {_return}")
        return _return
    return _inner


def federated(func):
    @wraps(func)
    def _inner(*args, **kwargs):
        federated_response = func(*args, **kwargs)
        schedule_logger(kwargs.get("job_id")).info(f"job command '{func.__name__}' return: {federated_response}")
        return return_federated_response(federated_response)
    return _inner


def federated_task(func):
    @wraps(func)
    def _inner(*args, **kwargs):
        task_id = kwargs.get("task_id")
        tasks = get_tasks_by_task_id(task_id)
        if tasks:
            _return = func(tasks=tasks, *args, **kwargs)
            schedule_logger(tasks[0]["job_id"]).info(f"task command '{func.__name__}' return: {_return}")
            return _return
        else:
            schedule_logger().exception(f"{func.__name__} no found task by task id {task_id}")
    return _inner


def return_federated_response(federated_response):
    retcode_set = set()
    for dest_role in federated_response.keys():
        for party_id in federated_response[dest_role].keys():
            retcode_set.add(federated_response[dest_role][party_id]["code"])
    if len(retcode_set) == 1 and Code.SUCCESS in retcode_set:
        federated_scheduling_status_code = FederatedSchedulingStatusCode.SUCCESS
    else:
        federated_scheduling_status_code = FederatedSchedulingStatusCode.FAILED
    return federated_scheduling_status_code, federated_response


class FederatedScheduler:
    """
    Send commands to party or scheduler
    """
    # Job
    @classmethod
    @federated
    def create_job(cls, job_id, roles, job_info):
        return RuntimeConfig.SCHEDULE_CLIENT.federated.create_job(job_id, roles, command_body=job_info)

    @classmethod
    @federated
    def sync_job_status(cls, job_id, roles, job_info):
        return RuntimeConfig.SCHEDULE_CLIENT.federated.sync_job_status(job_id, roles, job_info)

    @classmethod
    @federated
    def resource_for_job(cls, job_id, roles, operation_type):
        return RuntimeConfig.SCHEDULE_CLIENT.federated.resource_for_job(job_id, roles, operation_type)

    @classmethod
    @federated
    def start_job(cls, job_id, roles):
        return RuntimeConfig.SCHEDULE_CLIENT.federated.start_job(job_id, roles)

    @classmethod
    @federated
    def stop_job(cls, job_id, roles):
        return RuntimeConfig.SCHEDULE_CLIENT.federated.stop_job(job_id, roles)

    @classmethod
    @federated
    def update_job(cls, job_id, roles, command_body=None):
        return RuntimeConfig.SCHEDULE_CLIENT.federated.update_job(job_id, roles, command_body)

    @classmethod
    @federated
    def save_pipelined_model(cls, job_id, roles):
        return RuntimeConfig.SCHEDULE_CLIENT.federated.save_pipelined_model(job_id, roles)

    # task
    @classmethod
    @federated_task
    @federated
    def collect_task(cls, task_id, tasks=None):
        return RuntimeConfig.SCHEDULE_CLIENT.federated.collect_task(tasks=tasks)

    @classmethod
    @federated_task
    def sync_task_status(cls, task_id, tasks, command_body):
        return RuntimeConfig.SCHEDULE_CLIENT.federated.sync_task_status(tasks=tasks, command_body=command_body)

    @classmethod
    @federated_task
    def stop_task(cls, task_id,  command_body=None, tasks=None):
        return RuntimeConfig.SCHEDULE_CLIENT.federated.stop_task(tasks=tasks,
                                                                 command_body=command_body)

    @classmethod
    @federated_task
    @federated
    def start_task(cls, task_id, tasks=None):
        return RuntimeConfig.SCHEDULE_CLIENT.federated.start_task(tasks=tasks)

    @classmethod
    @federated_task
    @federated
    def rerun_task(cls, task_id, task_version, tasks=None):
        return RuntimeConfig.SCHEDULE_CLIENT.federated.rerun_task(tasks=tasks, task_version=task_version)

    # scheduler
    @classmethod
    @schedule_job
    def request_create_job(cls, party_id, command_body):
        return RuntimeConfig.SCHEDULE_CLIENT.scheduler.create_job(party_id, command_body)

    @classmethod
    @schedule_job
    def request_stop_job(cls, party_id, job_id, stop_status=None):
        command_body = {"job_id": job_id}
        if stop_status:
            command_body = {
                "stop_status": stop_status
            }
        return RuntimeConfig.SCHEDULE_CLIENT.scheduler.stop_job(party_id, command_body)

    @classmethod
    @schedule_job
    def request_rerun_job(cls, party_id, job_id):
        command_body = {"job_id": job_id}
        return RuntimeConfig.SCHEDULE_CLIENT.scheduler.rerun_job(party_id, command_body)

    @classmethod
    @schedule_job
    def report_task_to_scheduler(cls, party_id, command_body):
        return RuntimeConfig.SCHEDULE_CLIENT.scheduler.report_task(party_id, command_body)
