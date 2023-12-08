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
import json
import logging
import sys
import time
import traceback

from fate_flow.engine.backend._base import LocalEngine
from fate_flow.entity.spec.dag import TaskConfigSpec
from fate_flow.entity.types import BaseStatus, TaskStatus
from fate_flow.manager.worker.fate_executor import FateSubmit

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


class Deepspeed(LocalEngine):
    def run(self,  output_path, engine_run, run_parameters, session_id, **kwargs):
        parameters = TaskConfigSpec.parse_obj(run_parameters)
        env_name = "FATE_TASK_CONFIG"
        self.start_submit(session_id, parameters, engine_run, env_name)
        status = self.wait_deepspeed_job(session_id=session_id, timeout=engine_run.get("timeout", 36000))
        logger.info(f"deepspeed task end with status {status}")
        if status not in EndStatus.status_list():
            logger.info(f"start to kill deepspeed {session_id} task")
            self.kill(session_id=session_id)
            return -1
        # download result to output_path
        pass
        return 0

    @classmethod
    def start_submit(cls, session_id, parameters: TaskConfigSpec, engine_run, env_name):
        from eggroll.deepspeed.submit import client
        client = client.DeepspeedJob(session_id=session_id)
        world_size = engine_run.get("cores", 1)
        timeout_seconds = engine_run.get("timeout_seconds", 21600)
        resource_exhausted_strategy = engine_run.get("resource_exhausted_strategy", "waiting")
        options = {
            "eggroll.container.deepspeed.script.path": sys.modules[FateSubmit.__module__].__file__
        }
        resource_options = {"timeout_seconds": timeout_seconds, "resource_exhausted_strategy": resource_exhausted_strategy}
        resource_options.update(engine_run)
        command_arguments = cls.generate_command_arguments(env_name)
        environment_variables = {env_name: json.dumps(parameters.dict())}
        logger.info(f"world size {world_size}")
        logger.info(f"command_arguments: {command_arguments}")
        logger.info(f"environment_variables: {environment_variables}")
        logger.info(f"resource_options: {resource_options}")
        logger.info(f"options: {options}")
        logger.info(f"start submit deepspeed task {session_id}")
        client.submit(
            world_size=world_size,
            command_arguments=command_arguments,
            environment_variables=environment_variables,
            files={},
            resource_options=resource_options,
            options=options
        )
        logger.info(f"submit deepspeed task success")

    def wait_deepspeed_job(self, session_id, timeout=36000):
        if timeout < 0:
            return

        while True:
            status = self.query_status(session_id=session_id)
            if timeout % 100 == 0:
                logger.info(f"deepspeed task status {status}")
            timeout -= 1
            if timeout == 0:
                logger.error(f"task timeout, total {timeout}s")
                return status
            elif status in EndStatus.status_list():
                return status
            time.sleep(1)

    @staticmethod
    def generate_command_arguments(env_name, output_path=""):
        command_arguments = [
            "component",
            "execute",
            "--env-name",
            env_name,
            "--execution-final-meta-path",
            output_path
        ]
        return command_arguments

    def _cleanup1(self, session_id, task_info, **kwargs):
        self.kill(session_id)

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

    def query_status(self, session_id):
        status = self._query_status(session_id)
        if status in EndStatus.status_list():
            if status in [EndStatus.FINISHED]:
                return TaskStatus.SUCCESS
            else:
                return TaskStatus.FAILED
