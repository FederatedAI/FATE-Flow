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

from fate_flow.utils.base_utils import fate_uuid
from fate_flow.utils.file_utils import get_fate_flow_directory


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
        #todo: there is duplication in the case of multiple instances deployment
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
    return os.path.join(get_fate_flow_directory(), 'jobs', job_id, *args)


def get_job_log_directory(job_id, *args):
    return os.path.join(get_fate_flow_directory(), 'logs', job_id, *args)


def get_task_directory(job_id, role, party_id, task_name, task_id, task_version, **kwargs):
    return get_job_directory(job_id, role, party_id, task_name, task_id, str(task_version))


def start_session_stop(task):
    # todo: session stop
    pass


def get_general_worker_directory(worker_name, worker_id, *args):
    return os.path.join(get_fate_flow_directory(), worker_name, worker_id, *args)


def get_general_worker_log_directory(worker_name, worker_id, *args):
    return os.path.join(get_fate_flow_directory(), 'logs', worker_name, worker_id, *args)


def generate_model_info(job_id):
    model_id = job_id
    model_version = 0
    return model_id, model_version
