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
import time
import traceback

from fate_flow.engine.backend._base import LocalEngine
from fate_flow.entity.types import BaseStatus, TaskStatus
from fate_flow.utils import job_utils
from fate_flow.worker.fate_executor import FateSubmit

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

    def run(self,  output_path, conf_path, session_id, task_info, launcher_conf, **kwargs):
        logger.info("deepspeed task start")
        command_arguments = self.generate_command_arguments(conf_path, output_path)

        resource_options = {"timeout_seconds": launcher_conf.get("timeout"), "resource_exhausted_strategy": "waiting"}
        options = {"eggroll.container.deepspeed.script.path": sys.modules[FateSubmit.__module__].__file__}
        world_size = launcher_conf.get("world_size")
        logger.info(f"command_arguments: {command_arguments}\n resource_options: {resource_options}\n "
                    f"options: {options}\n world_size: {world_size}")

        from eggroll.deepspeed.submit import client
        # set session id == party task id
        client = client.DeepspeedJob(session_id)

        resp = client.submit(
            world_size=world_size,
            command_arguments=command_arguments,
            environment_variables={},
            files={},
            resource_options=resource_options,
            options=options
        )
        logger.info(f"submit deepspeed {resp.session_id} task success")

        status = self.wait_deepspeed_job(session_id=session_id, timeout=launcher_conf.get("timeout"))
        logger.info(f"deepspeed task end with status {status}")
        if status not in EndStatus.status_list():
            logger.info(f"start to kill deepspeed task {session_id}")
            self.kill(session_id=session_id)

        # download logs and models
        self.download_to(session_id, task_info)

    def wait_deepspeed_job(self, session_id, timeout):
        while True:
            status = self.query_status(session_id=session_id)
            if timeout % 10 == 0:
                logger.info(f"deepspeed task status {status}")
            timeout -= 1
            if timeout == 0:
                return status
            elif status in EndStatus.status_list():
                return status
            time.sleep(2)

    @staticmethod
    def generate_command_arguments(conf_path, output_path=""):
        command_arguments = [
            "component",
            "execute",
            "---config",
            conf_path,
            "FATE_TASK_CONFIG",
            "--execution-final-meta-path",
            output_path
        ]
        return command_arguments

    def _cleanup1(self, session_id, task_info, **kwargs):
        self.kill(session_id)
        self.download_to(session_id, task_info)

    @staticmethod
    def kill(session_id):
        if session_id:
            logger.info(f"start kill deepspeed task {session_id}")
            from eggroll.deepspeed.submit import client
            client = client.DeepspeedJob(session_id)
            try:
                client.kill()
            except Exception as e:
                traceback.format_exc()
                logger.error(e)

    @staticmethod
    def _query_status(session_id):
        if session_id:
            from eggroll.deepspeed.submit import client
            client = client.DeepspeedJob(session_id)
            _s = client.query_status().status
            return _s if _s else StatusSet.NEW
        return StatusSet.NEW

    @staticmethod
    def _download_job(session_id, base_dir, content_type=None, ranks: list = None):
        from eggroll.deepspeed.submit import client
        if not content_type:
            content_type = client.ContentType.ALL
        if session_id:
            client = client.DeepspeedJob(session_id)
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
        status = self._query_status(task)
        if status in StatusSet.status_list():
            if status in EndStatus.status_list():
                return False
            else:
                return True
        else:
            raise RuntimeError(f"task run status: {status}")

    def download(self, session_id, base_dir, content_type=None, ranks=None):
        from eggroll.deepspeed.submit.client import ContentType
        if not content_type:
            content_type = ContentType.ALL
        dir_name = self._download_job(session_id, base_dir, content_type, ranks)
        if dir_name:
            for file in os.listdir(dir_name):
                if file.endswith(".zip"):
                    rank_dir = os.path.join(dir_name, file.split(".zip")[0])
                    os.makedirs(rank_dir, exist_ok=True)
                    self.unzip(os.path.join(dir_name, file), extra_dir=rank_dir)
                    os.remove(os.path.join(dir_name, file))

    def download_to(self, session_id, task_info):
        try:
            logger.info(f"end task")
            path = self.download_model(session_id=session_id, task_info=task_info)
            logger.info(f"download model to {path}")
            path = self.download_log(session_id=session_id, task_info=task_info)
            logger.info(f"download logs to {path}")
        except Exception as e:
            traceback.format_exc()
            logger.error(e)

    def download_log(self, session_id, task_info, path=None):
        from eggroll.deepspeed.submit.client import ContentType
        if not path:
            path = self.log_path(task_info)
        self.download(session_id, base_dir=path, content_type=ContentType.LOGS)
        return path

    def download_model(self, session_id, task_info, path=None):
        from eggroll.deepspeed.submit.client import ContentType
        if not path:
            path = self.model_path(task_info)
        self.download(session_id, base_dir=path, content_type=ContentType.MODELS, ranks=[0])
        return path

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
    def model_path(task_info,):
        return os.path.join(job_utils.get_task_directory(**task_info, output=True), "model")

    @staticmethod
    def log_path(task_info):
        return job_utils.get_job_log_directory(
            task_info.get("job_id"), task_info.get("role"), task_info.get("party_id"), task_info.get("task_name")
        )
