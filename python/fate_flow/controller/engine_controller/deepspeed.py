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
from abc import ABC

from fate_flow.controller.engine_controller.engine import EngineABC
from fate_flow.db.db_models import Task
from fate_flow.db.job_default_config import JobDefaultConfig
from fate_flow.entity.run_status import BaseStatus, TaskStatus
from fate_flow.entity.types import WorkerName
from fate_flow.manager.worker_manager import WorkerManager
from fate_flow.utils import log_utils
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
    def run(self, task: Task, run_parameters, run_parameters_path, config_dir, log_dir, cwd_dir, **kwargs):
        from eggroll.deepspeed.submit import client
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
        cmd = [str(_c) for _c in command_arguments]
        environment_variables = {}
        files = {}
        options = {
            "eggroll.container.deepspeed.script.path": sys.modules[TaskExecutor.__module__].__file__
        }
        task_conf = run_parameters.role_parameter("task_conf", role=task.f_role, party_id=task.f_party_id)
        world_size = task_conf.get(task.f_component_name).get("world_size", JobDefaultConfig.task_world_size)
        resource_options = {"timeout_seconds": 3000, "resource_exhausted_strategy": "waiting"}
        schedule_logger(task.f_job_id).info(f"start submit deepspeed task")
        schedule_logger(task.f_job_id).info(f"cmd: {cmd}")
        client = client.DeepspeedJob()
        result = client.submit(
            world_size=world_size,
            command_arguments=cmd,
            environment_variables=environment_variables,
            files=files,
            resource_options=resource_options,
            options=options)
        return {"worker_id": worker_id, "cmd": cmd, "deepspeed_id": result.session_id}

    def kill(self, task):
        if task.f_deepspeed_id:
            from eggroll.deepspeed.submit import client
            client = client.DeepspeedJob(task.f_deepspeed_id)
            return client.kill()

    @staticmethod
    def _query_status(task):
        if task.f_deepspeed_id:
            from eggroll.deepspeed.submit import client
            client = client.DeepspeedJob(task.f_deepspeed_id)
            return client.query_status().status
        return StatusSet.NEW

    @staticmethod
    def _download_job(task):
        if task.f_deepspeed_id:
            from eggroll.deepspeed.submit import client
            client = client.DeepspeedJob(task.f_deepspeed_id)
            dir_name = os.path.join(log_utils.get_logger_base_dir(), task.f_job_id, task.f_role, task.f_party_id, task.f_component_name)
            os.makedirs(dir_name, exist_ok=True)
            path = lambda rank: f"{dir_name}/{rank}.zip"
            client.download_job_to(rank_to_path=path)
            return dir_name

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

    def download(self, task):
        dir_name = self._download_job(task)
        if dir_name:
            for file in os.listdir(dir_name):
                if file.endswith(".zip"):
                    rank_dir = os.path.join(dir_name, file.split(".zip")[0])
                    os.makedirs(rank_dir, exist_ok=True)
                    self.unzip(os.path.join(dir_name, file), extra_dir=rank_dir)
                    os.remove(os.path.join(dir_name, file))

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
