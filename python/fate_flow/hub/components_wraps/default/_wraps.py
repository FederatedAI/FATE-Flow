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

from fate_flow.engine.backend import build_backend
from fate_flow.entity.spec import TaskConfigSpec, ModelWarehouseChannelSpec, RuntimeTaskOutputChannelSpec
from fate_flow.hub.components_wraps import WrapsABC


class FlowWraps(WrapsABC):
    def __init__(self, config: TaskConfigSpec):
        self.config = config
        self.mlmd = self.load_mlmd(config.conf.mlmd)
        self.backend = build_backend(backend_name=self.config.conf.computing.type)

    @property
    def task_info(self):
        return {
            "job_id": self.config.job_id,
            "role": self.config.role,
            "party_id": self.config.party_id,
            "task_name": self.config.task_name,
            "task_id": self.config.task_id,
            "task_version": self.config.task_version
        }

    def run(self):
        _config = self.preprocess()
        _p = self.run_component()
        self.push_output()

    def preprocess(self):
        task_artifacts = {}
        logging.info(self.config.inputs.artifacts)
        for k, v in self.config.inputs.artifacts.items():
            if isinstance(v, dict):
                task_artifacts[k] = v
            else:
                if isinstance(v, ModelWarehouseChannelSpec):
                    self._input_model(v)
                else:
                    self._intput_data(v)

        # get component define
        define = self.backend.get_component_define(provider_name=self.config.provider_name, task_info=self.task_info)
        logging.info(define)
        logging.info(self.config.inputs.parameters)
        logging.info(self.config.inputs.artifacts)
        return {}

    def push_output(self):
        # report status
        logging.info("success")
        resp = self.mlmd.report_task_status(execution_id=self.config.party_task_id, status="success")
        logging.info(resp.text)

    def _intput_data(self, meta: RuntimeTaskOutputChannelSpec):
        logging.info(f"{meta.producer_task}, {meta.output_artifact_key}")
        resp = self.mlmd.query_data_tracking(
            job_id=self.config.job_id,
            role=self.config.role,
            party_id=self.config.party_id,
            task_name=meta.producer_task,
            output_key=meta.output_artifact_key
        )
        logging.info(resp.text)

    def _input_model(self, meta: ModelWarehouseChannelSpec):
        logging.info(meta)

    def _output_data(self):
        pass

    def _output_model(self):
        pass

    def _output_metric(self):
        pass

    def _output_logs(self):
        pass

    def run_component(self):
        task_parameters = self.config.dict()
        logging.info(self.config.provider_name)
        logging.info(self.task_info)
        logging.info("start run task")

        p = self.backend.run(
            provider_name=self.config.provider_name,
            task_info=self.task_info,
            run_parameters=task_parameters,
            output_path=""
        )
        p.wait()

        logging.info(f"p.stdout: {p.stdout}")
        logging.info(f"p.stderr: {p.stderr}")

    @staticmethod
    def load_mlmd(mlmd):
        if mlmd.type == "flow":
            from ofx.api.client import FlowSchedulerApi
            client = FlowSchedulerApi(
                host=mlmd.metadata.get("host"),
                port=mlmd.metadata.get("port"),
                protocol=mlmd.metadata.get("protocol"),
                api_version=mlmd.metadata.get("api_version"))
            return client.worker
