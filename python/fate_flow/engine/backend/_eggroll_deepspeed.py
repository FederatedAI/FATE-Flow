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
import os.path
import sys
import time
import traceback

from fate_flow.engine.backend._base import LocalEngine
from fate_flow.engine.devices.deepspeed import EggrollDeepspeedEngine
from fate_flow.entity.spec.dag import TaskConfigSpec, ComponentOutputMeta, ArtifactOutputSpec
from fate_flow.entity.types import BaseStatus, TaskStatus, ComputingEngine
from fate_flow.manager.outputs.data import DataManager
from fate_flow.manager.worker.fate_ds_executor import FateSubmit
from fate_flow.runtime.system_settings import COMPUTING_CONF, DEEPSPEED_RESULT_PLACEHOLDER, MODEL_STORE_PATH, \
    DEEPSPEED_LOGS_DIR_PLACEHOLDER, DEEPSPEED_MODEL_DIR_PLACEHOLDER
from fate_flow.utils.job_utils import generate_deepspeed_id

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
    def run(self,  output_path, engine_run, run_parameters, session_id, task_info, **kwargs):
        parameters = TaskConfigSpec.parse_obj(run_parameters)
        env_name = "FATE_TASK_CONFIG"
        self.start_submit(session_id, parameters, engine_run, env_name)
        status = self.wait_deepspeed_job(session_id=session_id, timeout=engine_run.get("timeout", 36000))
        logger.info(f"deepspeed task end with status {status}")
        engine = EggrollDeepspeedEngine()
        if status not in EndStatus.status_list():
            logger.info(f"start to kill deepspeed {session_id} task")
            self.kill(session_id=session_id)
            return -1
        logger.info(f"start download task result to dir {os.path.dirname(output_path)}")
        engine.download_result(
            worker_id=generate_deepspeed_id(parameters.party_task_id),
            path=os.path.dirname(output_path)
        )
        logger.info(f"start download task model")
        output_meta = None
        logger.info(f"{output_path}: {os.path.exists(output_path)}")
        if os.path.exists(output_path):
            with open(output_path, "r") as f:
                try:
                    result = json.load(f)
                    output_meta = ComponentOutputMeta.parse_obj(result)
                except:
                    logger.info(f"load output path {output_path} failed")
        logger.info(output_meta)
        if output_meta:
            if output_meta.status.code != 0:
                raise RuntimeError(output_meta.dict())
            for _key, _model in output_meta.io_meta.outputs.model.items():
                model = ArtifactOutputSpec(**_model)
                _, address = DataManager.uri_to_address(model.uri)
                path = os.path.join(MODEL_STORE_PATH, address.path.split("models/")[-1])
                logger.info(f"download model to {path}")
                engine.download_model_do(worker_id=session_id, path=path)
        logger.info("download model success")
        return 0

    @classmethod
    def start_submit(cls, session_id, parameters: TaskConfigSpec, engine_run, env_name):
        from eggroll.deepspeed.submit import client
        host = COMPUTING_CONF.get(ComputingEngine.EGGROLL).get("host")
        port = COMPUTING_CONF.get(ComputingEngine.EGGROLL).get("port")
        client = client.DeepspeedJob(session_id=session_id, host=host, port=port)
        world_size = engine_run.get("cores", 1)
        timeout_seconds = engine_run.get("timeout_seconds", 21600)
        resource_exhausted_strategy = engine_run.get("resource_exhausted_strategy", "waiting")
        options = {
            "eggroll.container.deepspeed.script.path": sys.modules[FateSubmit.__module__].__file__
        }
        resource_options = {"timeout_seconds": timeout_seconds, "resource_exhausted_strategy": resource_exhausted_strategy}
        resource_options.update(engine_run)
        command_arguments = cls.generate_command_arguments(env_name)
        environment_variables = {
            env_name: json.dumps(parameters.dict()),
            "DEEPSPEED_LOGS_DIR_PLACEHOLDER": DEEPSPEED_LOGS_DIR_PLACEHOLDER,
            "DEEPSPEED_MODEL_DIR_PLACEHOLDER": DEEPSPEED_MODEL_DIR_PLACEHOLDER,
            "DEEPSPEED_RESULT_PLACEHOLDER": DEEPSPEED_RESULT_PLACEHOLDER
        }
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
            status = self._query_status(session_id=session_id)
            if timeout % 5 == 0:
                logger.info(f"task status: {status}")
            timeout -= 1
            if timeout == 0:
                logger.error(f"task timeout, total {timeout}s")
                return status
            elif status in EndStatus.status_list():
                return status
            time.sleep(1)

    @staticmethod
    def generate_command_arguments(env_name, output_path=f"{DEEPSPEED_RESULT_PLACEHOLDER}/task_result.yaml"):
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
        # self.kill(session_id)
        pass

    @staticmethod
    def kill(session_id):
        if session_id:
            logger.info(f"start kill deepspeed task {session_id}")
            from eggroll.deepspeed.submit import client
            host = COMPUTING_CONF.get(ComputingEngine.EGGROLL).get("host")
            port = COMPUTING_CONF.get(ComputingEngine.EGGROLL).get("port")
            client = client.DeepspeedJob(session_id, host=host, port=port)
            try:
                client.kill()
            except Exception as e:
                traceback.format_exc()
                logger.error(e)

    @staticmethod
    def _query_status(session_id):
        if session_id:
            from eggroll.deepspeed.submit import client
            host = COMPUTING_CONF.get(ComputingEngine.EGGROLL).get("host")
            port = COMPUTING_CONF.get(ComputingEngine.EGGROLL).get("port")
            client = client.DeepspeedJob(session_id, host=host, port=port)
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
        return TaskStatus.RUNNING
