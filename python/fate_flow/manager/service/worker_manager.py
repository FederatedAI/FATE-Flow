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
import os
import sys
from uuid import uuid1

from ruamel import yaml

from fate_flow.db.base_models import DB, auto_date_timestamp_db_field
from fate_flow.db.db_models import Task, WorkerInfo
from fate_flow.entity.types import WorkerName
from fate_flow.runtime.runtime_config import RuntimeConfig
from fate_flow.utils import job_utils, process_utils
from fate_flow.utils.base_utils import current_timestamp, json_dumps
from fate_flow.utils.log_utils import failed_log, schedule_logger, start_log, successful_log


class WorkerManager:
    @classmethod
    def start_general_worker(cls, worker_name: WorkerName, job_id="", role="", party_id=0, provider=None,
                             initialized_config: dict = None, run_in_subprocess=True, **kwargs):
        pass

    @classmethod
    def start_task_worker(cls, worker_name, task: Task, task_parameters, executable, common_cmd=None,
                          extra_env: dict = None, **kwargs):
        worker_id, config_dir, log_dir = cls.get_process_dirs(
            worker_name=worker_name,
            job_id=task.f_job_id,
            role=task.f_role,
            party_id=task.f_party_id,
            task=task)
        params_env = cls.get_env(task.f_job_id, task_parameters)
        extra_env.update(params_env)
        if worker_name is WorkerName.TASK_EXECUTOR:
            from fate_flow.worker.fate_executor import FateSubmit
            module_file_path = sys.modules[FateSubmit.__module__].__file__
        else:
            raise Exception(f"not support {worker_name} worker")
        if executable:
            process_cmd = executable
        else:
            process_cmd = [os.getenv("EXECUTOR_ENV") or sys.executable or "python3"]
        process_cmd.extend(common_cmd)
        p = process_utils.run_subprocess(job_id=task.f_job_id, config_dir=config_dir, process_cmd=process_cmd,
                                         added_env=extra_env, log_dir=log_dir, cwd_dir=config_dir, process_name=worker_name.value,
                                         process_id=worker_id)
        cls.save_worker_info(task=task, worker_name=worker_name, worker_id=worker_id,
                             run_ip=RuntimeConfig.JOB_SERVER_HOST, run_pid=p.pid, config=task_parameters,
                             cmd=process_cmd)
        schedule_logger(job_id=task.f_job_id).info(f"start task worker, executor id {task.f_execution_id}...")
        return {
            "run_pid": p.pid,
            "run_ip": RuntimeConfig.JOB_SERVER_HOST,
            "worker_id": worker_id,
            "cmd": process_cmd,
            "run_port": RuntimeConfig.HTTP_PORT
        }

    @classmethod
    def get_process_dirs(cls, worker_name: WorkerName, worker_id=None, job_id=None, role=None, party_id=None, task: Task = None):
        if not worker_id:
            worker_id = uuid1().hex
        party_id = str(party_id)
        if task:
            config_dir = job_utils.get_job_directory(job_id, role, party_id, task.f_task_name, task.f_task_id,
                                                     str(task.f_task_version), worker_name.value, worker_id)
            log_dir = job_utils.get_job_log_directory(job_id, role, party_id, task.f_task_name)
        elif job_id and role and party_id:
            config_dir = job_utils.get_job_directory(job_id, role, party_id, worker_name.value, worker_id)
            log_dir = job_utils.get_job_log_directory(job_id, role, party_id, worker_name.value, worker_id)
        else:
            config_dir = job_utils.get_general_worker_directory(worker_name.value, worker_id)
            log_dir = job_utils.get_general_worker_log_directory(worker_name.value, worker_id)
        os.makedirs(config_dir, exist_ok=True)
        return worker_id, config_dir, log_dir

    @classmethod
    def get_config(cls, config_dir, config):
        config_path = os.path.join(config_dir, "config.json")
        with open(config_path, 'w') as fw:
            fw.write(json_dumps(config, indent=True))
        result_path = os.path.join(config_dir, "result.json")
        return config_path, result_path

    @classmethod
    def get_env(cls, job_id, task_parameters):
        # todo: api callback params
        env = {
            "FATE_JOB_ID": job_id,
            "FATE_TASK_CONFIG": yaml.dump(task_parameters),
        }
        return env

    @classmethod
    def cmd_to_func_kwargs(cls, cmd):
        kwargs = {}
        for i in range(2, len(cmd), 2):
            kwargs[cmd[i].lstrip("--")] = cmd[i+1]
        return kwargs

    @classmethod
    @DB.connection_context()
    def save_worker_info(cls, task: Task, worker_name: WorkerName, worker_id, **kwargs):
        worker = WorkerInfo()
        ignore_attr = auto_date_timestamp_db_field()
        for attr, value in task.to_dict().items():
            if hasattr(worker, attr) and attr not in ignore_attr and value is not None:
                setattr(worker, attr, value)
        worker.f_create_time = current_timestamp()
        worker.f_worker_name = worker_name.value
        worker.f_worker_id = worker_id
        for k, v in kwargs.items():
            attr = f"f_{k}"
            if hasattr(worker, attr) and v is not None:
                setattr(worker, attr, v)
        rows = worker.save(force_insert=True)
        if rows != 1:
            raise Exception("save worker info failed")

    @classmethod
    @DB.connection_context()
    def kill_task_all_workers(cls, task: Task):
        schedule_logger(task.f_job_id).info(start_log("kill all workers", task=task))
        workers_info = WorkerInfo.query(task_id=task.f_task_id, task_version=task.f_task_version, role=task.f_role,
                                        party_id=task.f_party_id)
        for worker_info in workers_info:
            schedule_logger(task.f_job_id).info(
                start_log(f"kill {worker_info.f_worker_name}({worker_info.f_run_pid})", task=task))
            try:
                cls.kill_worker(worker_info)
                schedule_logger(task.f_job_id).info(
                    successful_log(f"kill {worker_info.f_worker_name}({worker_info.f_run_pid})", task=task))
            except Exception as e:
                schedule_logger(task.f_job_id).warning(
                    failed_log(f"kill {worker_info.f_worker_name}({worker_info.f_run_pid})", task=task), exc_info=True)
        schedule_logger(task.f_job_id).info(successful_log("kill all workers", task=task))

    @classmethod
    def kill_worker(cls, worker_info: WorkerInfo):
        process_utils.kill_process(pid=worker_info.f_run_pid, expected_cmdline=worker_info.f_cmd)
