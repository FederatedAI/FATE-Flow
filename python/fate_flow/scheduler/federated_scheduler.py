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

from fate_flow.scheduler import SchedulerBase
from fate_flow.scheduler.client import SchedulerClient
from fate_flow.utils.api_utils import federated_api
from fate_flow.utils.log_utils import schedule_logger
from fate_flow.operation.job_saver import JobSaver
from fate_flow.entity.types import TaskCleanResourceType


def get_tasks_by_task_id(task_id):
    return [{"job_id": task.f_job_id, "role": task.f_role, "party_id": task.f_party_id,
             "component_name": task.f_component_name, "task_id": task.f_task_id,
             "task_version": task.f_task_version} for task in
            JobSaver.query_task(task_id=task_id, only_latest=True, is_scheduler=True)]


def federated_job(func):
    @wraps(func)
    def _inner(*args, **kwargs):
        _return = func(*args, **kwargs)
        schedule_logger(kwargs.get("job_id")).info(f"job command '{func.__name__}' return: {_return}")
        return _return
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


class FederatedScheduler(SchedulerBase):
    """
    Send commands to party,
    Report info to initiator
    """

    # Task
    REPORT_TO_INITIATOR_FIELDS = ["party_status", "start_time", "update_time", "end_time", "elapsed", "error_report"]

    # Job
    @classmethod
    @federated_job
    def create_job(cls, job_id, roles, job_info):
        return SchedulerClient.api.federated.create_job(job_id, roles, job_info)

    @classmethod
    @federated_job
    def update_parameter(cls, job_id, roles, updated_parameters):
        return SchedulerClient.api.federated.update_parameter(job_id, roles, updated_parameters)

    @classmethod
    @federated_job
    def resource_for_job(cls, job_id, roles, operation_type):
        return SchedulerClient.api.federated.resource_for_job(job_id, roles, operation_type)

    @classmethod
    @federated_job
    def check_component(cls, job_id, roles, check_type):
        return SchedulerClient.api.federated.check_component(job_id, roles, check_type)

    @classmethod
    @federated_job
    def dependence_for_job(cls, job_id, roles):
        return SchedulerClient.api.federated.dependence_for_job(job_id, roles)

    @classmethod
    @federated_job
    def connect(cls, job_id, roles, command_body):
        return SchedulerClient.api.federated.connect(job_id, roles, command_body)

    @classmethod
    @federated_job
    def start_job(cls, job_id, roles, command_body=None):
        return SchedulerClient.api.federated.start_job(job_id, roles, command_body)

    @classmethod
    @federated_job
    def align_args(cls, job_id, roles, command_body):
        return SchedulerClient.api.federated.align_args(job_id, roles, command_body)

    @classmethod
    @federated_job
    def sync_job(cls, job_id, roles, command_body=None):
        return SchedulerClient.api.federated.sync_job(job_id, roles, command_body)

    @classmethod
    @federated_job
    def sync_job_status(cls, job_id, roles, status, command_body=None):
        return SchedulerClient.api.federated.sync_job_status(job_id, roles, status, command_body)

    @classmethod
    @federated_job
    def save_pipelined_model(cls, job_id, roles):
        return SchedulerClient.api.federated.save_pipelined_model(job_id, roles)

    @classmethod
    @federated_job
    def stop_job(cls, job_id, roles, stop_status):
        return SchedulerClient.api.federated.stop_job(job_id, roles, stop_status)

    @classmethod
    @federated_job
    def request_create_job(cls, party_id, command_body):
        return SchedulerClient.api.scheduler.create_job(party_id, command_body)

    @classmethod
    @federated_job
    def request_stop_job(cls, party_id, job_id, stop_status):
        command_body = {
            "job_id": job_id,
            "stop_status": stop_status
        }
        return SchedulerClient.api.scheduler.stop_job(party_id, command_body)

    @classmethod
    @federated_job
    def request_rerun_job(cls, job, command_body):
        return SchedulerClient.api.scheduler.rerun_job()

    @classmethod
    @federated_job
    def clean_job(cls, job_id, roles, command_body):
        return SchedulerClient.api.federated.clean_job(job_id, roles, command_body)

    @classmethod
    @federated_task
    def create_task(cls, task_id=None, command_body=None, tasks=None):
        return SchedulerClient.api.federated.create_task(tasks=tasks, command_body=command_body)

    @classmethod
    @federated_task
    def start_task(cls, task_id, tasks=None):
        return SchedulerClient.api.federated.start_task(tasks=tasks)

    @classmethod
    @federated_task
    def collect_task(cls, task_id, tasks=None):
        return SchedulerClient.api.federated.collect_task(tasks=tasks)

    @classmethod
    @federated_task
    def sync_task_status(cls, task_id, status, tasks=None):
        return SchedulerClient.api.federated.sync_task_status(tasks=tasks, status=status)

    @classmethod
    @federated_task
    def stop_task(cls, task_id, stop_status, command_body=None, tasks=None):
        return SchedulerClient.api.federated.stop_task(tasks=tasks, stop_status=stop_status, command_body=command_body)

    @classmethod
    @federated_task
    def clean_task(cls, task_id, content_type: TaskCleanResourceType, tasks=None):
        return SchedulerClient.api.federated.clean_task(tasks=tasks, content_type=content_type.value)

    @classmethod
    def report_task_to_scheduler(cls, party_id, command_body):
        return SchedulerClient.api.scheduler.report_task(party_id=party_id, command_body=command_body)

    @classmethod
    def report_task_to_driver(cls, task_info):
        return SchedulerClient.api.worker.report_task()

    @classmethod
    def tracker_command(cls, job, request_data, command, json_body=None):
        job_parameters = job.f_runtime_conf_on_party["job_parameters"]
        response = federated_api(job_id=str(request_data['job_id']),
                                 method='POST',
                                 endpoint='/tracker/{}/{}/{}/{}/{}'.format(
                                     request_data['job_id'],
                                     request_data['component_name'],
                                     request_data['role'],
                                     request_data['party_id'],
                                     command),
                                 src_party_id=job.f_party_id,
                                 dest_party_id=request_data['party_id'],
                                 src_role=job.f_role,
                                 json_body=json_body if json_body else {},
                                 federated_mode=job_parameters["federated_mode"])
        return response
