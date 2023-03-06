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
import logging

from fate_flow.components.loader.mlmd.protocol import IOManagerProtocol, MLMD
from fate_flow.entity.types import TaskStatus, EndStatus


class ExecutionStatus:
    def __init__(self, task_id, client) -> None:
        self._task_id = task_id
        self.client = client

    def log_excution_start(self):
        return self._log_state(TaskStatus.RUNNING)

    def log_excution_end(self):
        return self._log_state(TaskStatus.SUCCESS)

    def log_excution_exception(self, message: dict):
        return self._log_state(TaskStatus.FAILED, message)

    def _log_state(self, state, message=None):
        error = ""
        if message:
            error = message.get("exception")
        response = self.client.worker.report_task_status(execution_id=self._task_id, status=state, error=error)
        logging.debug(f"response: {response.text}")

    def _get_state(self):
        response = self.client.worker.query_task_status(execution_id=self._task_id)
        logging.debug(f"response: {response.text}")
        status = False
        try:
            task_status = response.json().get("data").get("status")
            if task_status in EndStatus.status_list():
                status = True
        except Exception as e:
            logging.exception(e)
            status = True
        return status

    def safe_terminate(self):
        return self._get_state()


class IOManager(IOManagerProtocol):
    def __init__(self, task_id, client):
        self.task_id = task_id
        self.client = client

    def log_output_artifact(self, key, value):
        if value is None:
            return
        from fate_flow.components import DatasetArtifact, MetricArtifact, ModelArtifact

        if isinstance(value, DatasetArtifact):
            self.log_output_data(key, value)
        elif isinstance(value, ModelArtifact):
            self.log_output_model(key, value)
        elif isinstance(value, MetricArtifact):
            self.log_output_metric(key, value)
        else:
            raise RuntimeError(f"not supported input artifact `name={key}, value={value}`")

    def log_output_data(self, key, value):
        data = {
                   "output_key": value.name,
                   "meta_data": value.metadata,
                   "execution_id": self.task_id,
                   "uri": value.uri,
                   "type": "data",
               }
        logging.debug(f"log output data: {data}")
        response = self.client.worker.log_output_artifacts(**data)
        logging.debug(f"response: {response.text}")

    def log_output_model(self, key, value, metadata={}):
        data = {
            "output_key": value.name,
            "meta_data": value.metadata,
            "execution_id": self.task_id,
            "uri": value.uri,
            "type": "model",
        }
        logging.debug(f"log output model: {data}")
        response = self.client.worker.log_output_artifacts(**data)
        logging.debug(f"response: {response.text}")

    def log_output_metric(self, key, value):
        logging.debug(value)

    def safe_terminate(self):
        pass


class FlowMLMD(MLMD):
    def __init__(self, task_id):
        self._taskid = task_id
        self.worker_client = None
        self.init_worker_client()
        self.execution_status = ExecutionStatus(task_id, self.worker_client)
        self.io = IOManager(task_id=task_id, client=self.worker_client)


    def init_worker_client(self):
        from fate_flow.settings import HOST, HTTP_PORT, API_VERSION, HTTP_REQUEST_TIMEOUT, PROXY_PROTOCOL
        from ofx.api.client import FlowSchedulerApi
        self.worker_client = FlowSchedulerApi(host=HOST, port=HTTP_PORT, protocol=PROXY_PROTOCOL,
                                              api_version=API_VERSION, timeout=HTTP_REQUEST_TIMEOUT,
                                              remote_protocol=None, remote_host=None,
                                              remote_port=None, grpc_channel=None)
