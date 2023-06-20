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
import json
import logging
import os.path
import sys
import traceback

from fate_flow.engine.backend import build_backend
from fate_flow.entity.spec.dag import PreTaskConfigSpec, DataWarehouseChannelSpec, ComponentIOArtifactsTypeSpec,\
    TaskConfigSpec
from fate_flow.entity.spec.dag._artifact import ArtifactInputApplySpec, Metadata, RuntimeTaskOutputChannelSpec, \
    ArtifactOutputApplySpec
from fate_flow.entity.spec.dag._output import ComponentOutputMeta
from fate_flow.entity.types import DataframeArtifactType, TableArtifactType, TaskStatus, ComputingEngine

from fate_flow.hub.components_wraps import WrapsABC
from fate_flow.runtime.system_settings import STANDALONE_DATA_HOME
from fate_flow.utils import job_utils


class FlowWraps(WrapsABC):
    def __init__(self, config: PreTaskConfigSpec):
        self.config = config
        self.mlmd = self.load_mlmd(config.mlmd)
        self.backend = build_backend(backend_name=self.config.conf.computing.type)

    @property
    def task_info(self):
        return {
            "component": self.config.component,
            "job_id": self.config.job_id,
            "role": self.config.role,
            "party_id": self.config.party_id,
            "task_name": self.config.task_name,
            "task_id": self.config.task_id,
            "task_version": self.config.task_version
        }

    def run(self):
        code = 0
        exceptions = ""
        try:
            config = self.preprocess()
            output_meta = self.run_component(config)
            self.push_output(output_meta)
            code, exceptions = output_meta.status.code, output_meta.status.exceptions
        except Exception as e:
            traceback.format_exc()
            code = -1
            exceptions = str(e)
        finally:
            self.report_status(code, exceptions)

    def preprocess(self):
        # input
        logging.info(self.config.input_artifacts)
        input_artifacts = self._preprocess_input_artifacts()
        logging.info(input_artifacts)

        # output
        output_artifacts = self._preprocess_output_artifacts()
        logging.info(output_artifacts)
        config = TaskConfigSpec(
            job_id=self.config.job_id,
            task_id=self.config.task_id,
            party_task_id=self.config.party_task_id,
            component=self.config.component,
            role=self.config.role,
            party_id=self.config.party_id,
            stage=self.config.stage,
            parameters=self.config.parameters,
            input_artifacts=input_artifacts,
            output_artifacts=output_artifacts,
            conf=self.config.conf
        )
        logging.info(config)
        return config

    def run_component(self, config):
        task_parameters = config.dict()
        logging.info("start run task")
        task_dir = job_utils.get_task_directory(**self.task_info)
        os.makedirs(task_dir, exist_ok=True)
        task_result = os.path.join(task_dir, "task_result.yaml")
        p = self.backend.run(
            provider_name=self.config.provider_name,
            task_info=self.task_info,
            run_parameters=task_parameters,
            output_path=task_result
        )
        p.wait()
        logging.info("finish task")
        if os.path.exists(task_result):
            with open(task_result, "r") as f:
                result = json.load(f)
                output_meta = ComponentOutputMeta.parse_obj(result)
                logging.info(output_meta)
        else:
            output_meta = ComponentOutputMeta(status=ComponentOutputMeta.status(code=1, exceptions=p.stdout))
        return output_meta

    def push_output(self, output_meta: ComponentOutputMeta):
        if self.task_end_with_success(output_meta.status.code):
            pass
        self.report_status(output_meta.status.code, output_meta.status.exceptions)

    def _preprocess_input_artifacts(self):
        input_artifacts = {}
        if self.config.input_artifacts.data:
            for _k, _channels in self.config.input_artifacts.data.items():
                input_artifacts[_k] = None
                if isinstance(_channels, list):
                    input_artifacts[_k] = []
                    for _channel in _channels:
                        input_artifacts[_k].append(self._intput_data_artifacts(_channel))
                else:
                    input_artifacts[_k] = self._intput_data_artifacts(_channels)
        return input_artifacts

    def _preprocess_output_artifacts(self):
        # get component define
        logging.debug("get component define")
        define = self.component_define
        logging.info(f"component define: {define}")
        output_artifacts = {}
        if not define:
            return output_artifacts
        else:
            # data
            for key in define.outputs.dict().keys():
                datas = getattr(define.outputs, key, None)
                if datas:
                    for data in datas:
                        output_artifacts[data.name] = self._output_artifacts(data.type_name, data.is_multi, data.name)
        return output_artifacts

    def _output_artifacts(self, type_name, is_multi, name):
        output_artifacts = ArtifactOutputApplySpec(uri="")
        if type_name in [DataframeArtifactType.type_name, TableArtifactType.type_name]:
            if self.config.conf.computing.type == ComputingEngine.STANDALONE:
                os.environ["STANDALONE_DATA_PATH"] = STANDALONE_DATA_HOME
                uri = f"{self.config.conf.computing.type}://{STANDALONE_DATA_HOME}{self.config.job_id}/{self.config.party_task_id}"
            else:
                uri = f"{self.config.conf.computing.type}:///{self.config.job_id}/{self.config.party_task_id}"
            if is_multi:
                uri += "_{index}"
        else:
            uri = job_utils.get_job_directory(self.config.job_id, self.config.task_name, str(self.config.task_version),
                                              "output", name)
            if not is_multi:
                uri = os.path.join(f"file:///{uri}", type_name)
        output_artifacts.uri = uri
        return output_artifacts

    @property
    def component_define(self):
        define = self.backend.get_component_define(
            provider_name=self.config.provider_name,
            task_info=self.task_info,
            stage=self.config.stage
        )
        if define:
            return ComponentIOArtifactsTypeSpec(**define)
        else:
            return None

    def _intput_data_artifacts(self, channel):
        meta = ArtifactInputApplySpec(metadata=Metadata(metadata={}), uri="")
        if isinstance(channel, DataWarehouseChannelSpec):
            if channel.name and channel.namespace:
                resp = self.mlmd.query_data_meta(
                    namespace=channel.namespace,
                    name=channel.name
                )
                logging.info(resp.text)
                resp_json = resp.json()
                logging.info(meta)
                meta.metadata.metadata = {"schema": resp_json.get("data", {}).get("meta", {})}
                meta.uri = resp_json.get("data", {}).get("path")
            else:
                resp = self.mlmd.query_data_meta(
                    job_id=channel.namespace,
                    name=channel.name
                )

        elif isinstance(channel, RuntimeTaskOutputChannelSpec):
            pass
            # resp = self.mlmd.query_data_tracking(
            #     job_id=self.config.job_id,
            #     role=self.config.role,
            #     party_id=self.config.party_id,
            #     task_name=channel.producer_task,
            #     output_key=channel.output_artifact_key
            # )
            # logging.info(resp.text)
        return meta

    def report_status(self, code, error=""):
        if self.task_end_with_success(code):
            resp = self.mlmd.report_task_status(
                execution_id=self.config.party_task_id,
                status=TaskStatus.SUCCESS
            )
        else:
            resp = self.mlmd.report_task_status(
                execution_id=self.config.party_task_id,
                status=TaskStatus.FAILED,
                error=error
            )
        logging.info(resp.text)

    @staticmethod
    def task_end_with_success(code):
        return code == 0

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
