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
import datetime
import os
import threading

import yaml

from fate_flow.db.base_models import DB
from fate_flow.db.db_models import Job, Task
from fate_flow.entity.spec.dag import InheritConfSpec
from fate_flow.entity.types import TaskStatus
from fate_flow.errors.server_error import InheritanceFailed
from fate_flow.manager.operation.job_saver import JobSaver
from fate_flow.runtime.system_settings import LOG_DIR, JOB_DIR, WORKERS_DIR
from fate_flow.utils.base_utils import fate_uuid, current_timestamp
from fate_flow.utils.log_utils import schedule_logger


class JobIdGenerator(object):
    _lock = threading.RLock()

    def __init__(self, initial_value=0):
        self._value = initial_value
        self._pre_timestamp = None
        self._max = 99999

    def next_id(self):
        """
        generate next job id with locking
        """
        now = datetime.datetime.now()
        with JobIdGenerator._lock:
            if self._pre_timestamp == now:
                if self._value < self._max:
                    self._value += 1
                else:
                    now += datetime.timedelta(microseconds=1)
                    self._pre_timestamp = now
                    self._value = 0
            else:
                self._pre_timestamp = now
                self._value = 0
            return "{}{}".format(now.strftime("%Y%m%d%H%M%S%f"), self._value)


job_id_generator = JobIdGenerator()


def generate_job_id():
    return job_id_generator.next_id()


def generate_task_id(job_id, component_name):
    return '{}_{}'.format(job_id, component_name)


def generate_task_version_id(task_id, task_version):
    return "{}_{}".format(task_id, task_version)


def generate_session_id(task_id, task_version, role, party_id, suffix=None, random_end=False):
    items = [task_id, str(task_version), role, party_id]
    if suffix:
        items.append(suffix)
    if random_end:
        items.append(fate_uuid())
    return "_".join(items)


def get_job_directory(job_id, *args):
    return os.path.join(JOB_DIR, job_id, *args)


def get_job_log_directory(job_id, *args):
    return os.path.join(LOG_DIR, job_id, *args)


def get_task_directory(job_id, role, party_id, task_name, task_version, input=False, output=False, **kwargs):
    if input:
        return get_job_directory(job_id, role, party_id, task_name, str(task_version), "input")
    if output:
        return get_job_directory(job_id, role, party_id, task_name, str(task_version), "output")
    else:
        return get_job_directory(job_id, role, party_id, task_name, str(task_version))


def get_general_worker_directory(worker_name, worker_id, *args):
    return os.path.join(WORKERS_DIR, worker_name, worker_id, *args)


def get_general_worker_log_directory(worker_name, worker_id, *args):
    return os.path.join(LOG_DIR, worker_name, worker_id, *args)


def generate_model_info(job_id):
    model_id = job_id
    model_version = "0"
    return model_id, model_version


@DB.connection_context()
def get_job_resource_info(job_id, role, party_id):
    jobs = Job.select(Job.f_cores, Job.f_memory).where(
        Job.f_job_id == job_id,
        Job.f_role == role,
        Job.f_party_id == party_id)
    if jobs:
        job = jobs[0]
        return job.f_cores, job.f_memory
    else:
        return None, None


@DB.connection_context()
def get_task_resource_info(job_id, role, party_id, task_id, task_version):
    tasks = Task.select(Task.f_task_cores, Task.f_memory).where(
        Task.f_job_id == job_id,
        Task.f_role == role,
        Task.f_party_id == party_id,
        Task.f_task_id == task_id,
        Task.f_task_version == task_version
    )
    if tasks:
        task = tasks[0]
        return task.f_task_cores, task.f_memory
    else:
        return None, None


def save_job_dag(job_id, dag):
    job_conf_file = os.path.join(JOB_DIR, job_id, "dag.yaml")
    os.makedirs(os.path.dirname(job_conf_file), exist_ok=True)
    with open(job_conf_file, "w") as f:
        f.write(yaml.dump(dag))


def inheritance_check(inheritance: InheritConfSpec = None):
    if not inheritance:
        return
    if not inheritance.task_list:
        raise InheritanceFailed(
            task_list=inheritance.task_list,
            position="dag_schema.dag.conf.inheritance.task_list"
        )
    inheritance_jobs = JobSaver.query_job(job_id=inheritance.job_id)
    inheritance_tasks = JobSaver.query_task(job_id=inheritance.job_id)
    if not inheritance_jobs:
        raise InheritanceFailed(job_id=inheritance.job_id, detail=f"no found job {inheritance.job_id}")
    task_status = {}
    for task in inheritance_tasks:
        task_status[task.f_task_name] = task.f_status

    for task_name in inheritance.task_list:
        if task_name not in task_status.keys():
            raise InheritanceFailed(job_id=inheritance.job_id, task_name=task_name, detail="no found task name")
        elif task_status[task_name] not in [TaskStatus.SUCCESS, TaskStatus.PASS]:
            raise InheritanceFailed(
                job_id=inheritance.job_id,
                task_name=task_name,
                task_status=task_status[task_name],
                detail=f"task status need in [{TaskStatus.SUCCESS}, {TaskStatus.PASS}]"
            )


def check_task_is_timeout(task: Task):
    now_time = current_timestamp()
    running_time = (now_time - task.f_create_time)/1000
    if task.f_timeout and running_time > task.f_timeout:
        schedule_logger(task.f_job_id).info(f'task {task.f_task_name} run time {running_time}s timeout')
        return True
    else:
        return False
