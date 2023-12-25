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
import logging
import os
import subprocess
import sys
from uuid import uuid1

from fate_flow.runtime.system_settings import ENGINES
from ruamel import yaml

from fate_flow.db.base_models import DB, auto_date_timestamp_db_field
from fate_flow.db.db_models import Task, WorkerInfo
from fate_flow.entity.types import WorkerName, EngineType, ComputingEngine
from fate_flow.runtime.runtime_config import RuntimeConfig
from fate_flow.utils import job_utils, process_utils
from fate_flow.utils.base_utils import current_timestamp, json_dumps
from fate_flow.utils.log_utils import failed_log, schedule_logger, start_log, successful_log


class WorkerManager:
    @classmethod
    def start_task_worker(cls, worker_name, task_info, task_parameters=None, executable=None, common_cmd=None,
                          extra_env: dict = None, record=False, stderr=None, sync=False, config_dir=None, std_dir=None,
                          **kwargs):
        if not extra_env:
            extra_env = {}
        worker_id = uuid1().hex
        if not config_dir or not std_dir:
            config_dir, std_dir = cls.get_process_dirs(
                job_id=task_info.get("job_id"),
                role=task_info.get("role"),
                party_id=task_info.get("party_id"),
                task_name=task_info.get("task_name"),
                task_version=task_info.get("task_version")
            )
        params_env = {}
        if task_parameters:
            params_env = cls.get_env(task_info.get("job_id"), task_parameters)
        extra_env.update(params_env)
        if executable:
            process_cmd = executable
        else:
            process_cmd = [os.getenv("EXECUTOR_ENV") or sys.executable or "python3"]
        process_cmd.extend(common_cmd)
        if sync and cls.worker_outerr_with_pipe(worker_name):
            stderr = subprocess.PIPE
        p = process_utils.run_subprocess(job_id=task_info.get("job_id"), config_dir=config_dir, process_cmd=process_cmd,
                                         added_env=extra_env, std_dir=std_dir, cwd_dir=config_dir,
                                         process_name=worker_name.value, stderr=stderr)
        if record:
            cls.save_worker_info(task_info=task_info, worker_name=worker_name, worker_id=worker_id,
                                 run_ip=RuntimeConfig.JOB_SERVER_HOST, run_pid=p.pid, config=task_parameters,
                                 cmd=process_cmd)
            return {
                "run_pid": p.pid,
                "run_ip": RuntimeConfig.JOB_SERVER_HOST,
                "worker_id": worker_id,
                "cmd": process_cmd,
                "run_port": RuntimeConfig.HTTP_PORT
            }
        else:
            if sync:
                error_io = io.BytesIO()
                if cls.worker_outerr_with_pipe(worker_name):
                    while True:
                        output = p.stderr.readline()
                        if output == b'' and p.poll() is not None:
                            break
                        if output:
                            error_io.write(output)
                error_io.seek(0)
                _code = p.wait()
                _e = error_io.read()
                if _e and _code:
                    logging.error(f"process {worker_name.value} run error[code:{_code}]\n: {_e.decode()}")
            return p

    @classmethod
    def worker_outerr_with_pipe(cls, worker_name):
        return worker_name == WorkerName.TASK_EXECUTE and \
               ENGINES.get(EngineType.COMPUTING) not in [ComputingEngine.SPARK]

    @classmethod
    def get_process_dirs(cls, job_id, role, party_id, task_name, task_version):
        config_dir = job_utils.get_job_directory(job_id, role, party_id, task_name, str(task_version))
        std_dir = job_utils.get_job_log_directory(job_id, role, party_id, task_name, "stdout")
        os.makedirs(config_dir, exist_ok=True)
        return config_dir, std_dir

    @classmethod
    def get_config(cls, config_dir, config):
        config_path = os.path.join(config_dir, "config.json")
        with open(config_path, 'w') as fw:
            fw.write(json_dumps(config, indent=True))
        result_path = os.path.join(config_dir, "result.json")
        return config_path, result_path

    @classmethod
    def get_env(cls, job_id, task_parameters):
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
    def save_worker_info(cls, task_info, worker_name: WorkerName, worker_id, **kwargs):
        worker = WorkerInfo()
        ignore_attr = auto_date_timestamp_db_field()
        for attr, value in task_info.items():
            attr = f"f_{attr}"
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
