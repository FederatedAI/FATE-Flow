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
import typing

from fate_flow.db.db_models import Job, Task


def ready_log(msg, job: Job = None, task: Task = None, role=None, party_id=None, detail=None):
    prefix, suffix = base_msg(job, task, role, party_id, detail)
    return f"{prefix}{msg} ready{suffix}"


def start_log(msg, job: Job = None, task: Task = None, role=None, party_id=None, detail=None):
    prefix, suffix = base_msg(job, task, role, party_id, detail)
    return f"{prefix}start to {msg}{suffix}"


def successful_log(msg, job: Job = None, task: Task = None, role=None, party_id=None, detail=None):
    prefix, suffix = base_msg(job, task, role, party_id, detail)
    return f"{prefix}{msg} successfully{suffix}"


def failed_log(msg, job: Job = None, task: Task = None, role=None, party_id=None, detail=None):
    prefix, suffix = base_msg(job, task, role, party_id, detail)
    return f"{prefix}failed to {msg}{suffix}"


def base_msg(job: Job = None, task: Task = None, role: str = None, party_id: typing.Union[str, int] = None, detail=None):
    if detail:
        detail_msg = f" detail: \n{detail}"
    else:
        detail_msg = ""
    if task is not None:
        return f"task {task.f_task_id} {task.f_task_version} ", f" on {task.f_role} {task.f_party_id}{detail_msg}"
    elif job is not None:
        return "", f" on {job.f_role} {job.f_party_id}{detail_msg}"
    elif role and party_id:
        return "", f" on {role} {party_id}{detail_msg}"
    else:
        return "", f"{detail_msg}"
