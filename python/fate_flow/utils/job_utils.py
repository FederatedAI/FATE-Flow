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
import errno
import os
import sys
import threading
import typing

from fate_arch.common import FederatedMode, file_utils
from fate_arch.common.base_utils import current_timestamp, fate_uuid, json_dumps
from fate_flow.db.db_models import DB, Job, Task
from fate_flow.db.db_utils import query_db
from fate_flow.db.job_default_config import JobDefaultConfig
from fate_flow.db.service_registry import ServiceRegistry
from fate_flow.entity import JobConfiguration, RunParameters
from fate_flow.entity.run_status import JobStatus, TaskStatus
from fate_flow.settings import FATE_BOARD_DASHBOARD_ENDPOINT
from fate_flow.utils import detect_utils, process_utils, session_utils
from fate_flow.utils.base_utils import get_fate_flow_directory
from fate_flow.utils.log_utils import schedule_logger
from fate_flow.utils.schedule_utils import get_dsl_parser_by_version


class JobIdGenerator(object):
    _lock = threading.RLock()

    def __init__(self, initial_value=0):
        self._value = initial_value
        self._pre_timestamp = None
        self._max = 99999

    def next_id(self):
        '''
        generate next job id with locking
        '''
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
    items = [task_id, str(task_version), role, str(party_id)]
    if suffix:
        items.append(suffix)
    if random_end:
        items.append(fate_uuid())
    return "_".join(items)


def generate_task_input_data_namespace(task_id, task_version, role, party_id):
    return "input_data_{}".format(generate_session_id(task_id=task_id,
                                                      task_version=task_version,
                                                      role=role,
                                                      party_id=party_id))


def get_job_directory(job_id, *args):
    return os.path.join(get_fate_flow_directory(), 'jobs', job_id, *args)


def get_job_log_directory(job_id, *args):
    return os.path.join(get_fate_flow_directory(), 'logs', job_id, *args)


def get_task_directory(job_id, role, party_id, component_name, task_id, task_version, **kwargs):
    return get_job_directory(job_id, role, party_id, component_name, task_id, task_version)


def get_general_worker_directory(worker_name, worker_id, *args):
    return os.path.join(get_fate_flow_directory(), worker_name, worker_id, *args)


def get_general_worker_log_directory(worker_name, worker_id, *args):
    return os.path.join(get_fate_flow_directory(), 'logs', worker_name, worker_id, *args)


def check_config(config: typing.Dict, required_parameters: typing.List):
    for parameter in required_parameters:
        if parameter not in config:
            return False, 'configuration no {} parameter'.format(parameter)
    else:
        return True, 'ok'


def check_job_runtime_conf(runtime_conf: typing.Dict):
    detect_utils.check_config(runtime_conf, ['initiator', 'role'])
    detect_utils.check_config(runtime_conf['initiator'], ['role', 'party_id'])
    # deal party id
    runtime_conf['initiator']['party_id'] = int(runtime_conf['initiator']['party_id'])
    for r in runtime_conf['role'].keys():
        for i in range(len(runtime_conf['role'][r])):
            runtime_conf['role'][r][i] = int(runtime_conf['role'][r][i])


def runtime_conf_basic(if_local=False):
    job_runtime_conf = {
        "dsl_version": 2,
        "initiator": {},
        "job_parameters": {
            "common": {
                "federated_mode": FederatedMode.SINGLE
            },
        },
        "role": {},
        "component_parameters": {}
    }
    if if_local:
        job_runtime_conf["initiator"]["role"] = "local"
        job_runtime_conf["initiator"]["party_id"] = 0
        job_runtime_conf["role"]["local"] = [0]
    return job_runtime_conf


def new_runtime_conf(job_dir, method, module, role, party_id):
    if role:
        conf_path_dir = os.path.join(job_dir, method, module, role, str(party_id))
    else:
        conf_path_dir = os.path.join(job_dir, method, module, str(party_id))
    os.makedirs(conf_path_dir, exist_ok=True)
    return os.path.join(conf_path_dir, 'runtime_conf.json')


def save_job_conf(job_id, role, party_id, dsl, runtime_conf, runtime_conf_on_party, train_runtime_conf, pipeline_dsl=None):
    path_dict = get_job_conf_path(job_id=job_id, role=role, party_id=party_id)
    dump_job_conf(path_dict=path_dict,
                  dsl=dsl,
                  runtime_conf=runtime_conf,
                  runtime_conf_on_party=runtime_conf_on_party,
                  train_runtime_conf=train_runtime_conf,
                  pipeline_dsl=pipeline_dsl)
    return path_dict


def save_task_using_job_conf(task: Task):
    task_dir = get_task_directory(job_id=task.f_job_id,
                                  role=task.f_role,
                                  party_id=task.f_party_id,
                                  component_name=task.f_component_name,
                                  task_id=task.f_task_id,
                                  task_version=str(task.f_task_version))
    return save_using_job_conf(task.f_job_id, task.f_role, task.f_party_id, config_dir=task_dir)


def save_using_job_conf(job_id, role, party_id, config_dir):
    path_dict = get_job_conf_path(job_id=job_id, role=role, party_id=party_id, specified_dir=config_dir)
    job_configuration = get_job_configuration(job_id=job_id,
                                              role=role,
                                              party_id=party_id)
    dump_job_conf(path_dict=path_dict,
                  dsl=job_configuration.dsl,
                  runtime_conf=job_configuration.runtime_conf,
                  runtime_conf_on_party=job_configuration.runtime_conf_on_party,
                  train_runtime_conf=job_configuration.train_runtime_conf,
                  pipeline_dsl=None)
    return path_dict


def dump_job_conf(path_dict, dsl, runtime_conf, runtime_conf_on_party, train_runtime_conf, pipeline_dsl=None):
    os.makedirs(os.path.dirname(path_dict.get('dsl_path')), exist_ok=True)
    os.makedirs(os.path.dirname(path_dict.get('runtime_conf_on_party_path')), exist_ok=True)
    for data, conf_path in [(dsl, path_dict['dsl_path']),
                            (runtime_conf, path_dict['runtime_conf_path']),
                            (runtime_conf_on_party, path_dict['runtime_conf_on_party_path']),
                            (train_runtime_conf, path_dict['train_runtime_conf_path']),
                            (pipeline_dsl, path_dict['pipeline_dsl_path'])]:
        with open(conf_path, 'w+') as f:
            f.truncate()
            if not data:
                data = {}
            f.write(json_dumps(data, indent=4))
            f.flush()
    return path_dict


@DB.connection_context()
def get_job_configuration(job_id, role, party_id) -> JobConfiguration:
    jobs = Job.select(Job.f_dsl, Job.f_runtime_conf, Job.f_train_runtime_conf, Job.f_runtime_conf_on_party).where(Job.f_job_id == job_id,
                                                                                                                  Job.f_role == role,
                                                                                                                  Job.f_party_id == party_id)
    if jobs:
        job = jobs[0]
        return JobConfiguration(**job.to_human_model_dict())


def get_task_using_job_conf(task_info: dict):
    task_dir = get_task_directory(**task_info)
    return read_job_conf(task_info["job_id"], task_info["role"], task_info["party_id"], task_dir)


def read_job_conf(job_id, role, party_id, specified_dir=None):
    path_dict = get_job_conf_path(job_id=job_id, role=role, party_id=party_id, specified_dir=specified_dir)
    conf_dict = {}
    for key, path in path_dict.items():
        config = file_utils.load_json_conf(path)
        conf_dict[key.rstrip("_path")] = config
    return JobConfiguration(**conf_dict)


def get_job_conf_path(job_id, role, party_id, specified_dir=None):
    conf_dir = get_job_directory(job_id) if not specified_dir else specified_dir
    job_dsl_path = os.path.join(conf_dir, 'job_dsl.json')
    job_runtime_conf_path = os.path.join(conf_dir, 'job_runtime_conf.json')
    if not specified_dir:
        job_runtime_conf_on_party_path = os.path.join(conf_dir, role, str(party_id), 'job_runtime_on_party_conf.json')
    else:
        job_runtime_conf_on_party_path = os.path.join(conf_dir, 'job_runtime_on_party_conf.json')
    train_runtime_conf_path = os.path.join(conf_dir, 'train_runtime_conf.json')
    pipeline_dsl_path = os.path.join(conf_dir, 'pipeline_dsl.json')
    return {'dsl_path': job_dsl_path,
            'runtime_conf_path': job_runtime_conf_path,
            'runtime_conf_on_party_path': job_runtime_conf_on_party_path,
            'train_runtime_conf_path': train_runtime_conf_path,
            'pipeline_dsl_path': pipeline_dsl_path}


@DB.connection_context()
def get_upload_job_configuration_summary(upload_tasks: typing.List[Task]):
    jobs_run_conf = {}
    for task in upload_tasks:
        jobs = Job.select(Job.f_job_id, Job.f_runtime_conf_on_party, Job.f_description).where(Job.f_job_id == task.f_job_id)
        job = jobs[0]
        jobs_run_conf[job.f_job_id] = job.f_runtime_conf_on_party["component_parameters"]["role"]["local"]["0"]["upload_0"]
        jobs_run_conf[job.f_job_id]["notes"] = job.f_description
    return jobs_run_conf


@DB.connection_context()
def get_job_parameters(job_id, role, party_id):
    jobs = Job.select(Job.f_runtime_conf_on_party).where(Job.f_job_id == job_id,
                                                         Job.f_role == role,
                                                         Job.f_party_id == party_id)
    if jobs:
        job = jobs[0]
        return job.f_runtime_conf_on_party.get("job_parameters")
    else:
        return {}


@DB.connection_context()
def get_job_dsl(job_id, role, party_id):
    jobs = Job.select(Job.f_dsl).where(Job.f_job_id == job_id,
                                       Job.f_role == role,
                                       Job.f_party_id == party_id)
    if jobs:
        job = jobs[0]
        return job.f_dsl
    else:
        return {}


def job_pipeline_component_name():
    return "pipeline"


def job_pipeline_component_module_name():
    return "Pipeline"


@DB.connection_context()
def list_job(limit=0, offset=0, query=None, order_by=None):
    return query_db(Job, limit, offset, query, order_by)


@DB.connection_context()
def list_task(limit=0, offset=0, query=None, order_by=None):
    return query_db(Task, limit, offset, query, order_by)


def check_job_process(pid):
    if pid < 0:
        return False
    if pid == 0:
        raise ValueError('invalid PID 0')
    try:
        os.kill(pid, 0)
    except OSError as err:
        if err.errno == errno.ESRCH:
            # ESRCH == No such process
            return False
        elif err.errno == errno.EPERM:
            # EPERM clearly means there's a process to deny access to
            return True
        else:
            # According to "man 2 kill" possible error values are
            # (EINVAL, EPERM, ESRCH)
            raise
    else:
        return True


def check_job_is_timeout(job: Job):
    job_parameters = job.f_runtime_conf_on_party["job_parameters"]
    timeout = job_parameters.get("timeout", JobDefaultConfig.job_timeout)
    now_time = current_timestamp()
    running_time = (now_time - job.f_create_time)/1000
    if running_time > timeout:
        schedule_logger(job.f_job_id).info(f'run time {running_time}s timeout')
        return True
    else:
        return False


def start_session_stop(task):
    job_parameters = RunParameters(**get_job_parameters(job_id=task.f_job_id, role=task.f_role, party_id=task.f_party_id))
    session_manager_id = generate_session_id(task.f_task_id, task.f_task_version, task.f_role, task.f_party_id)
    if task.f_status != TaskStatus.WAITING:
        schedule_logger(task.f_job_id).info(f'start run subprocess to stop task sessions {session_manager_id}')
    else:
        schedule_logger(task.f_job_id).info(f'task is waiting, pass stop sessions {session_manager_id}')
        return
    task_dir = os.path.join(get_job_directory(job_id=task.f_job_id), task.f_role,
                            task.f_party_id, task.f_component_name, 'session_stop')
    os.makedirs(task_dir, exist_ok=True)
    process_cmd = [
        sys.executable or 'python3',
        sys.modules[session_utils.SessionStop.__module__].__file__,
        '--session', session_manager_id,
        '--computing', job_parameters.computing_engine,
        '--federation', job_parameters.federation_engine,
        '--storage', job_parameters.storage_engine,
        '-c', 'stop' if task.f_status == JobStatus.SUCCESS else 'kill'
    ]
    p = process_utils.run_subprocess(job_id=task.f_job_id, config_dir=task_dir, process_cmd=process_cmd)
    p.wait()
    p.poll()


def get_timeout(job_id, timeout, runtime_conf, dsl):
    try:
        if timeout > 0:
            schedule_logger(job_id).info(f'setting job timeout {timeout}')
            return timeout
        else:
            default_timeout = job_default_timeout(runtime_conf, dsl)
            schedule_logger(job_id).info(f'setting job timeout {timeout} not a positive number, using the default timeout {default_timeout}')
            return default_timeout
    except:
        default_timeout = job_default_timeout(runtime_conf, dsl)
        schedule_logger(job_id).info(f'setting job timeout {timeout} is incorrect, using the default timeout {default_timeout}')
        return default_timeout


def job_default_timeout(runtime_conf, dsl):
    # future versions will improve
    timeout = JobDefaultConfig.job_timeout
    return timeout


def get_board_url(job_id, role, party_id):
    board_url = "http://{}:{}{}".format(
        ServiceRegistry.FATEBOARD.get("host"),
        ServiceRegistry.FATEBOARD.get("port"),
        FATE_BOARD_DASHBOARD_ENDPOINT).format(job_id, role, party_id)
    return board_url


def check_job_inheritance_parameters(job, inheritance_jobs, inheritance_tasks):
    if not inheritance_jobs:
        raise Exception(
            f"no found job {job.f_inheritance_info.get('job_id')} role {job.f_role} party id {job.f_party_id}")
    inheritance_job = inheritance_jobs[0]
    task_status = {}
    for task in inheritance_tasks:
        task_status[task.f_component_name] = task.f_status
    for component in job.f_inheritance_info.get('component_list'):
        if component not in task_status.keys():
            raise Exception(f"job {job.f_inheritance_info.get('job_id')} no found component {component}")
        elif task_status[component] not in [TaskStatus.SUCCESS, TaskStatus.PASS]:
            raise Exception(F"job {job.f_inheritance_info.get('job_id')} component {component} status:{task_status[component]}")
    dsl_parser = get_dsl_parser_by_version()
    dsl_parser.verify_conf_reusability(inheritance_job.f_runtime_conf, job.f_runtime_conf, job.f_inheritance_info.get('component_list'))
    dsl_parser.verify_dsl_reusability(inheritance_job.f_dsl, job.f_dsl, job.f_inheritance_info.get('component_list', []))