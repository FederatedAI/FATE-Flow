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
import logging
import os
import sys
import traceback

from fate_flow.db import Task
from fate_flow.engine.devices.local import LocalEngine
from fate_flow.entity.types import BaseStatus, TaskStatus, WorkerName, StorageEngine
from fate_flow.manager.service.worker_manager import WorkerManager
from fate_flow.manager.worker.deepspeed_download_model import DownloadModel
from fate_flow.runtime.system_settings import MODEL_STORE_PATH, COMPUTING_CONF
from fate_flow.utils import job_utils, process_utils
from fate_flow.utils.job_utils import get_job_log_directory, generate_deepspeed_id
from fate_flow.utils.log_utils import schedule_logger

logger = logging.getLogger(__name__)


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


class EggrollDeepspeedEngine(LocalEngine):
    @staticmethod
    def generate_session_id():
        return f"deepspeed_session_{datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')}"

    def run(self,  task: Task, run_parameters, run_parameters_path, config_dir, log_dir, cwd_dir, **kwargs):
        schedule_logger(task.f_job_id).info("start to submit deepspeed task")
        run_info = WorkerManager.start_task_worker(
            worker_name=WorkerName.TASK_ENTRYPOINT,
            task_info=task.to_human_model_dict(),
            extra_env={"PYTHONPATH": self.provider.python_path},
            executable=[self.provider.python_env],
            common_cmd=self.generate_cmd(),
            task_parameters=run_parameters,
            record=True
        )
        run_info["worker_id"] = generate_deepspeed_id(run_parameters.get("party_task_id"))
        return run_info

    def cleanup(self, task: Task):
        self._cleanup(task, sync=True)
        self.kill(task)

    def kill(self, task):
        schedule_logger(task.f_job_id).info(f"start kill deepspeed task {task.f_worker_id}")
        from eggroll.deepspeed.submit import client

        host = COMPUTING_CONF.get(StorageEngine.EGGROLL).get("host")
        port = COMPUTING_CONF.get(StorageEngine.EGGROLL).get("port")

        client = client.DeepspeedJob(task.f_worker_id, host=host, port=port)
        try:
            client.kill()
        except Exception as e:
            traceback.format_exc()
            schedule_logger(task.f_job_id).error(e)

    def download_output(self, task: Task):
        try:
            schedule_logger(task.f_job_id).info(f"start download logs")
            self.download_log(task)
        except Exception as e:
            traceback.format_exc()
            schedule_logger(task.f_job_id).error(e)

    @staticmethod
    def _query_status(session_id):
        if session_id:
            from eggroll.deepspeed.submit import client
            host = COMPUTING_CONF.get(StorageEngine.EGGROLL).get("host")
            port = COMPUTING_CONF.get(StorageEngine.EGGROLL).get("port")
            client = client.DeepspeedJob(session_id, host=host, port=port)
            _s = client.query_status().status
            return _s if _s else StatusSet.NEW
        return StatusSet.NEW

    def query_task_status(self, task):
        status = self._query_status(task.f_worker_id)
        if status in EndStatus.status_list():
            if status in [EndStatus.FINISHED]:
                return TaskStatus.SUCCESS
            else:
                return TaskStatus.FAILED

    @staticmethod
    def _download_job(session_id, base_dir, content_type=None, ranks: list = None):
        from eggroll.deepspeed.submit import client
        if not content_type:
            content_type = client.ContentType.ALL
        if session_id:
            host = COMPUTING_CONF.get(StorageEngine.EGGROLL).get("host")
            port = COMPUTING_CONF.get(StorageEngine.EGGROLL).get("port")
            client = client.DeepspeedJob(session_id, host=host, port=port)
            os.makedirs(base_dir, exist_ok=True)
            path = lambda rank: f"{base_dir}/{rank}.zip"
            client.download_job_to(rank_to_path=path, content_type=content_type, ranks=ranks)
            return base_dir

    def query_status(self, session_id):
        status = self._query_status(session_id)
        if status in EndStatus.status_list():
            if status in [EndStatus.FINISHED]:
                return TaskStatus.SUCCESS
            else:
                return TaskStatus.FAILED

    def is_alive(self, task):
        status = self._query_status(task.f_worker_id)
        if status in StatusSet.status_list():
            if status in EndStatus.status_list():
                return False
            else:
                return True
        else:
            raise RuntimeError(f"task run status: {status}")

    def download(self, base_dir, content_type=None, ranks=None, worker_id=None, only_rank_0=False):
        from eggroll.deepspeed.submit.client import ContentType
        if not content_type:
            content_type = ContentType.ALL
        session_id = worker_id
        dir_name = self._download_job(session_id, base_dir, content_type, ranks)
        if dir_name:
            for file in os.listdir(dir_name):
                if file.endswith(".zip"):
                    if only_rank_0:
                        rank_dir = dir_name
                    else:
                        rank_dir = os.path.join(dir_name, file.split(".zip")[0])
                    os.makedirs(rank_dir, exist_ok=True)
                    self.unzip(os.path.join(dir_name, file), extra_dir=rank_dir)
                    os.remove(os.path.join(dir_name, file))

    def download_log(self, task, path=None):
        from eggroll.deepspeed.submit.client import ContentType
        if not path:
            path = self.log_path(task)
        schedule_logger(task.f_job_id).info(f"download logs to {path}")
        self.download(worker_id=task.f_worker_id, base_dir=path, content_type=ContentType.LOGS)

    def download_result(self, path, worker_id):
        from eggroll.deepspeed.submit.client import ContentType
        self.download(
            worker_id=worker_id, base_dir=path, content_type=ContentType.RESULT, ranks=[0],
            only_rank_0=True
        )

    @staticmethod
    def download_model(task_info, path=""):
        # run subprocess to download model
        process_cmd = [
            sys.executable or 'python3',
            sys.modules[DownloadModel.__module__].__file__,
            '--job_id', task_info.get("job_id"),
            '--role', task_info.get("role"),
            '--party_id', task_info.get("party_id"),
            '--task_id', task_info.get("task_id"),
            '--task_version', task_info.get("task_version"),
            "--path", path
        ]
        process_name = "model_download"
        log_dir = conf_dir = job_utils.get_job_log_directory(task_info.get("job_id"), task_info.get("role"), task_info.get("party_id"), task_info.get("task_name"))
        p = process_utils.run_subprocess(
            job_id=task_info.get("job_id"),
            config_dir=conf_dir,
            process_cmd=process_cmd,
            std_dir=log_dir,
            process_name=process_name
        )
        schedule_logger(task_info.get("job_id")).info(f"download model process id: {p.pid}")

    def download_model_do(self, task=None, worker_id=None, path=None):
        from eggroll.deepspeed.submit.client import ContentType
        if not path:
            path = self.model_path(task)
        self.download(worker_id=worker_id, base_dir=path, content_type=ContentType.MODELS, ranks=[0], only_rank_0=True)

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
    def model_path(task):
        _p = os.path.join(MODEL_STORE_PATH, task.f_job_id, task.f_role, task.f_party_id, task.f_task_name)
        return _p

    @staticmethod
    def log_path(task):
        return get_job_log_directory(task.f_job_id, task.f_role, task.f_party_id, task.f_task_name)
