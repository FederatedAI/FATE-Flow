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

from fate_flow.db.base_models import DB
from fate_flow.db.db_models import Job, Task
from fate_flow.entity.types import PROTOCOL
from fate_flow.errors.server_error import NoFoundTask
from fate_flow.manager.operation.base_saver import BaseSaver
from fate_flow.db.schedule_models import ScheduleJob, ScheduleTask, ScheduleTaskStatus


class JobSaver(BaseSaver):
    @classmethod
    def create_job(cls, job_info) -> Job:
        return cls._create_job(Job, job_info)

    @classmethod
    def create_task(cls, task_info) -> Task:
        return cls._create_task(Task, task_info)

    @classmethod
    def delete_job(cls, job_id):
        return cls._delete_job(Job, job_id)

    @classmethod
    def delete_task(cls, job_id):
        return cls._delete_job(Task, job_id)

    @classmethod
    def update_job_status(cls, job_info):
        return cls._update_job_status(Job, job_info)

    @classmethod
    def query_job(cls, reverse=None, order_by=None, **kwargs):
        return cls._query_job(Job, reverse, order_by, **kwargs)

    @classmethod
    def update_job(cls, job_info):
        return cls._update_job(Job, job_info)

    @classmethod
    def update_job_user(cls, job_id, user_name):
        return cls.update_entity_table(Job, {
            "job_id": job_id,
            "user_name": user_name
        }, filters=["job_id"])

    @classmethod
    def list_job(cls, limit, offset, query, order_by):
        return cls._list(Job, limit, offset, query, order_by)

    @classmethod
    def list_task(cls, limit, offset, query, order_by):
        return cls._list(Task, limit, offset, query, order_by)

    @classmethod
    def query_task(
            cls, only_latest=True, reverse=None, order_by=None, ignore_protocol=False, protocol=PROTOCOL.FATE_FLOW,
            **kwargs
    ):
        if not ignore_protocol:
            kwargs["protocol"] = protocol
        return cls._query_task(
            Task, only_latest=only_latest, reverse=reverse, order_by=order_by, **kwargs
        )

    @classmethod
    def query_task_by_execution_id(cls, execution_id):
        tasks = cls.query_task(execution_id=execution_id)
        if not tasks:
            raise NoFoundTask(execution_id=execution_id)
        return tasks[0]

    @classmethod
    def update_task_status(cls, task_info):
        return cls._update_task_status(Task, task_info)

    @classmethod
    def update_task(cls, task_info, report=False):
        return cls._update_task(Task, task_info, report)

    @classmethod
    def task_key(cls, task_id, role, party_id):
        return f"{task_id}_{role}_{party_id}"


class ScheduleJobSaver(BaseSaver):
    @classmethod
    def create_job(cls, job_info) -> ScheduleJob:
        return cls._create_job(ScheduleJob, job_info)

    @classmethod
    def create_task(cls, task_info) -> ScheduleTask:
        return cls._create_task(ScheduleTask, task_info)

    @classmethod
    def delete_job(cls, job_id):
        return cls._delete_job(ScheduleJob, job_id)

    @classmethod
    def update_job_status(cls, job_info):
        return cls._update_job_status(ScheduleJob, job_info)

    @classmethod
    def update_job(cls, job_info):
        return cls._update_job(ScheduleJob, job_info)

    @classmethod
    def query_job(cls, reverse=None, order_by=None, protocol=PROTOCOL.FATE_FLOW, **kwargs):
        return cls._query_job(ScheduleJob, reverse, order_by, protocol=protocol, **kwargs)

    @classmethod
    def query_task(cls, only_latest=True, reverse=None, order_by=None, scheduler_status=False, **kwargs):
        if not scheduler_status:
            obj = ScheduleTask
        else:
            obj = ScheduleTaskStatus
        return cls._query_task(obj, only_latest=only_latest, reverse=reverse, order_by=order_by,
                               scheduler_status=scheduler_status, **kwargs)

    @classmethod
    def update_task_status(cls, task_info, scheduler_status=False):
        if "party_status" in task_info:
            task_info["status"] = task_info["party_status"]
        task_obj = ScheduleTask
        if scheduler_status:
            task_obj = ScheduleTaskStatus
        return cls._update_task_status(task_obj, task_info)

    @classmethod
    def update_task(cls, task_info, report=False):
        cls._update_task(ScheduleTaskStatus, task_info, report)

    @classmethod
    @DB.connection_context()
    def get_status_tasks_asc(cls, job_id):
        tasks = ScheduleTaskStatus.query(order_by="create_time", reverse=False, job_id=job_id)
        tasks_group = cls.get_latest_tasks(tasks=tasks, scheduler_status=True)
        return tasks_group

    @classmethod
    def task_key(cls, task_id, role, party_id):
        return f"{task_id}_{role}_{party_id}"

    @classmethod
    def create_task_scheduler_status(cls, task_info):
        cls._create_entity(ScheduleTaskStatus, task_info)

    @classmethod
    def get_latest_scheduler_tasks(cls, tasks):
        tasks_group = {}
        for task in tasks:
            if task.f_task_id not in tasks_group:
                tasks_group[task.f_task_id] = task
            elif task.f_task_version > tasks_group[task.f_task_id].f_task_version:
                tasks_group[task.f_task_id] = task
        return tasks_group
