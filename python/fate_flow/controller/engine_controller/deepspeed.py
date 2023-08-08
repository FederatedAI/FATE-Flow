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
import datetime
import os
import sys
from abc import ABC

from fate_arch.common.base_utils import json_dumps
from fate_flow.controller.engine_controller.engine import EngineABC
from fate_flow.db.db_models import Task
from fate_flow.db.job_default_config import JobDefaultConfig
from fate_flow.db.runtime_config import RuntimeConfig
from fate_flow.entity.run_status import BaseStatus, TaskStatus
from fate_flow.entity.types import WorkerName
from fate_flow.manager.worker_manager import WorkerManager
from fate_flow.settings import EXTRA_MODEL_DIR
from fate_flow.utils import log_utils, job_utils, process_utils
from fate_flow.utils.deepspeed_utils import Submit
from fate_flow.utils.log_utils import detect_logger, schedule_logger
from fate_flow.worker.task_executor import TaskExecutor


class StatusSet(BaseStatus):
    NEW = "NEW"
    NEW_TIMEOUT = "NEW_TIMEOUT"
    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"
    KILLED = "KILLED"
    ERROR = "ERROR"
    FINISHED = "FINISHED"


class EndStatus(BaseStatus):
    NEW_TIMEOUT = StatusSet.NEW_TIMEOUT
    CLOSED = StatusSet.CLOSED
    FAILED = StatusSet.KILLED
    ERROR = StatusSet.ERROR
    FINISHED = StatusSet.FINISHED


class EggrollDeepspeedEngine(EngineABC, ABC):
    @staticmethod
    def generate_session_id():
        return f"deepspeed_session_{datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')}"

    def run(self, task: Task, run_parameters, run_parameters_path, config_dir, log_dir, cwd_dir, **kwargs):
        worker_id, config_dir, log_dir = WorkerManager.get_process_dirs(
            worker_name=WorkerName.TASK_EXECUTOR,
            job_id=task.f_job_id,
            role=task.f_role,
            party_id=task.f_party_id,
            task=task
        )
        config = run_parameters.to_dict()
        session_id, _, command_arguments = WorkerManager.generate_common_cmd(task, config_dir, config,
                                                                             log_dir, worker_id)
        command_arguments.extend(["--is_deepspeed", True])
        command_arguments.extend(["--model_path", self.model_path(task)])
        cmd = [str(_c) for _c in command_arguments]
        environment_variables = {}
        files = {}
        options = {
            "eggroll.container.deepspeed.script.path": sys.modules[TaskExecutor.__module__].__file__
        }
        task_conf = run_parameters.role_parameter("task_conf", role=task.f_role, party_id=task.f_party_id)
        world_size = task_conf.get(task.f_component_name).get("world_size", JobDefaultConfig.task_world_size)
        timeout = task_conf.get(task.f_component_name).get("timeout", JobDefaultConfig.resource_waiting_timeout)
        resource_options = {"timeout_seconds": timeout, "resource_exhausted_strategy": "waiting"}
        submit_conf = {
            "world_size": world_size,
            "command_arguments": cmd,
            "environment_variables": environment_variables,
            "files": files,
            "resource_options": resource_options,
            "options": options
        }
        config_dir = job_utils.get_task_directory(
            task.f_job_id, task.f_role, task.f_party_id,
            task.f_component_name, task.f_task_id, str(task.f_task_version)
        )
        os.makedirs(config_dir, exist_ok=True)
        config_path = os.path.join(config_dir, 'deepspeed_submit.json')
        with open(config_path, 'w') as fw:
            fw.write(json_dumps(submit_conf))
        session_id = self.generate_session_id()
        process_cmd, pid = self.submit(task, config_path, session_id, log_dir=log_dir)
        WorkerManager.save_worker_info(task=task, worker_name=WorkerName.TASK_EXECUTOR, worker_id=worker_id,
                                       run_ip=RuntimeConfig.JOB_SERVER_HOST, run_pid=pid, cmd=process_cmd)
        return {"worker_id": worker_id, "cmd": cmd, "deepspeed_id": session_id, "run_pid": pid}

    @staticmethod
    def submit(task, config_path, session_id, log_dir):
        conf_dir = job_utils.get_job_directory(job_id=task.f_job_id)
        os.makedirs(conf_dir, exist_ok=True)
        process_cmd = [
            sys.executable or 'python3',
            sys.modules[Submit.__module__].__file__,
            '--job_id', task.f_job_id,
            '--role', task.f_role,
            '--party_id', task.f_party_id,
            '--task_id', task.f_task_id,
            '--task_version', task.f_task_version,
            '--component_name', task.f_component_name,
            '--config', config_path,
            '--job_server', f"{RuntimeConfig.JOB_SERVER_HOST}:{RuntimeConfig.HTTP_PORT}",
            '--session_id', session_id,
            '--log_dir', log_dir,
            "--parent_log_dir", os.path.dirname(log_dir)
        ]
        process_name = "deepspeed_submit"
        log_dir = job_utils.get_job_log_directory(job_id=task.f_job_id)

        p = process_utils.run_subprocess(job_id=task.f_job_id, config_dir=conf_dir, process_cmd=process_cmd,
                                         log_dir=log_dir, process_name=process_name)
        schedule_logger(task.f_job_id).info(f"run subprocess {p.pid}")
        return process_cmd, p.pid

    def kill(self, task):
        if task.f_deepspeed_id:
            schedule_logger(task.f_job_id).info(f"start kill deepspeed task: {task.f_deepspeed_id}")
            from eggroll.deepspeed.submit import client
            client = client.DeepspeedJob(task.f_deepspeed_id)
            return client.kill()

    @staticmethod
    def _query_status(task):
        if task.f_deepspeed_id:
            from eggroll.deepspeed.submit import client
            client = client.DeepspeedJob(task.f_deepspeed_id)
            _s = client.query_status().status
            return _s if _s else StatusSet.NEW
        return StatusSet.NEW

    @staticmethod
    def _download_job(task, base_dir, content_type=None, ranks: list = None):
        from eggroll.deepspeed.submit import client
        if not content_type:
            content_type = client.ContentType.ALL
        if task.f_deepspeed_id:
            client = client.DeepspeedJob(task.f_deepspeed_id)
            os.makedirs(base_dir, exist_ok=True)
            path = lambda rank: f"{base_dir}/{rank}.zip"
            client.download_job_to(rank_to_path=path, content_type=content_type, ranks=ranks)
            return base_dir

    def query_task_status(self, task):
        status = self._query_status(task)
        if status in EndStatus.status_list():
            if status in [EndStatus.FINISHED]:
                return TaskStatus.SUCCESS
            else:
                return TaskStatus.FAILED

    def is_alive(self, task: Task):
        status = self._query_status(task)
        detect_logger(task.f_job_id).info(f"task {task.f_task_id} {task.f_task_version} deepspeed status {status}")
        if status in StatusSet.status_list():
            if status in EndStatus.status_list():
                return False
            else:
                return True
        else:
            raise RuntimeError(f"task run status: {status}")

    def download(self, task, base_dir, content_type=None, ranks=None):
        from eggroll.deepspeed.submit.client import ContentType
        if not content_type:
            content_type = ContentType.ALL
        dir_name = self._download_job(task, base_dir, content_type, ranks)
        if dir_name:
            for file in os.listdir(dir_name):
                if file.endswith(".zip"):
                    rank_dir = os.path.join(dir_name, file.split(".zip")[0])
                    os.makedirs(rank_dir, exist_ok=True)
                    self.unzip(os.path.join(dir_name, file), extra_dir=rank_dir)
                    os.remove(os.path.join(dir_name, file))

    def download_log(self, task, path=None):
        from eggroll.deepspeed.submit.client import ContentType
        if not path:
            path = self.log_path(task)
        self.download(task, base_dir=path, content_type=ContentType.LOGS)

    def download_model(self, task, path=None):
        from eggroll.deepspeed.submit.client import ContentType
        if not path:
            path = self.model_path(task, download=True)
        self.download(task, base_dir=path, content_type=ContentType.MODELS, ranks=[0])

    @staticmethod
    def unzip(zip_path, extra_dir):
        import zipfile
        zfile = zipfile.ZipFile(zip_path, "r")
        for name in zfile.namelist():
            dir_name = os.path.dirname(zip_path)
            file_path = os.path.join(dir_name, extra_dir, name)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            data = zfile.read(name)
            with open(file_path, "w+b") as file:
                file.write(data)

    @staticmethod
    def model_path(task, download=False):
        _p = os.path.join(EXTRA_MODEL_DIR, task.f_job_id, task.f_component_name)
        if not download:
            # only rank 0 output model
            _p = os.path.join(_p, "0")
        return _p

    @staticmethod
    def log_path(task):
        return os.path.join(
                log_utils.get_logger_base_dir(), task.f_job_id, task.f_role, task.f_party_id, task.f_component_name
        )
