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
import subprocess
import sys
import traceback
from urllib.parse import urlparse

import yaml

from fate_flow.adapter.bfia.settings import FATE_CONTAINER_HOME
from fate_flow.adapter.bfia.utils.entity.status import TaskStatus
from fate_flow.adapter.bfia.utils.spec.task import TaskRuntimeEnv
from fate_flow.engine.backend import build_backend
from fate_flow.entity.code import ReturnCode
from fate_flow.entity.spec.dag import TaskConfigSpec, ArtifactInputApplySpec, Metadata, ArtifactOutputApplySpec, \
    ComponentSpecV1, TaskRuntimeConfSpec, FlowLogger, StandaloneComputingSpec, OSXFederationSpec, ComponentOutputMeta, \
    ArtifactOutputSpec
from fate_flow.entity.types import ProviderName
from fate_flow.hub.components_wraps import WrapsABC
from fate_flow.manager.worker.fate_executor import FateSubmit
from fate_flow.runtime.system_settings import DEFAULT_OUTPUT_DATA_PARTITIONS
from ofx.api.client import BfiaSchedulerApi

logger = logging.getLogger(__name__)

COMPUTING_ENGINE = "standalone"


class BfiaWraps(WrapsABC):
    def __init__(self, config: TaskRuntimeEnv):
        self.config = config
        self.stages = ""
        self.backend = build_backend(backend_name=COMPUTING_ENGINE)
        self.io = DataIo(self.config.system.storage)
        self._partitions = DEFAULT_OUTPUT_DATA_PARTITIONS
        self._component_desc = None
        self._output_map = {}

    @property
    def mlmd(self):
        if self.config.system.callback:
            parsed_url = urlparse(self.config.system.callback)
            client = BfiaSchedulerApi(
                host=parsed_url.hostname,
                port=parsed_url.port)
            return client.worker

    @property
    def task_info(self):
        return {
            "job_id": "job",
            "role": self.self_role,
            "party_id": self.self_party_id,
            "task_id": self.config.config.task_id,
            "task_version": 0
        }

    @property
    def task_input_dir(self):
        task_id = self.config.config.task_id
        base_dir = FATE_CONTAINER_HOME
        if self.config.config.log and self.config.config.log.path:
            base_dir = self.config.config.log.path
        path = os.path.join(base_dir, "jobs", task_id, self.self_role, "input")
        os.makedirs(path, exist_ok=True)
        return path

    @property
    def task_output_dir(self):
        task_id = self.config.config.task_id
        base_dir = FATE_CONTAINER_HOME
        if self.config.config.log and self.config.config.log.path:
            base_dir = self.config.config.log.path
        path = os.path.join(base_dir, "jobs", task_id, self.self_role, "output")
        os.makedirs(path, exist_ok=True)
        return path

    @property
    def component_desc(self) -> ComponentSpecV1:
        if not self._component_desc:
            self.set_component_desc()
        return self._component_desc

    @property
    def self_role(self):
        return self.config.config.self_role.split(".")[0]

    @property
    def self_party_id(self):
        role, party_index = self.config.config.self_role.split(".")
        return self.config.config.node_id[role][party_index]

    @property
    def data_home(self):
        path = os.path.join(FATE_CONTAINER_HOME, "data")
        os.makedirs(path, exist_ok=True)
        return path

    @property
    def parties(self):
        parties_info = []
        for role, infos in self.config.config.node_id.items():
            for index, party_id in infos.items():
                parties_info.append({"role": role, "partyid": party_id})
        parties = {
            "local": {"role": self.self_role, "partyid": self.self_party_id},
            "parties": parties_info
        }
        return parties

    @property
    def generate_conf(self):
        return TaskRuntimeConfSpec(
            logger=self._generate_logger_conf(),
            device=self._generate_device(),
            computing=self._generate_computing_conf(),
            federation=self._generate_federation_conf(),
            storage=self.generate_storage_conf()
        )

    def task_logs_dir(self, *args):
        task_id = self.config.config.task_id
        base_dir = FATE_CONTAINER_HOME
        if self.config.config.log and self.config.config.log.path:
            base_dir = self.config.config.log.path
        path = os.path.join(base_dir, "logs",task_id, *args)
        os.makedirs(path, exist_ok=True)
        return path

    def cleanup(self):
        pass

    def run(self):
        code = 0
        try:
            config = self.preprocess()
            output_meta = self.run_component(config)
            self.push_output(output_meta)
            print(output_meta)
            code = output_meta.status.code
            if output_meta.status.code != ReturnCode.Base.SUCCESS:
                code = ReturnCode.Task.COMPONENT_RUN_FAILED
                exceptions = output_meta.status.exceptions
                logger.error(exceptions)
        except Exception as e:
            traceback.format_exc()
            code = ReturnCode.Task.TASK_RUN_FAILED
            print(e)
            logger.error(e)
        finally:
            print(f"finish task with code {code}")
            self.report_status(code)
            if code:
                sys.exit(code)

    def preprocess(self):
        # set log
        print("start preprocess")
        self._generate_logger_conf().install()
        logger = logging.getLogger(__name__)

        # input
        logger.info("start generating input artifacts")
        logger.info(self.config)
        input_artifacts = self._preprocess_input_artifacts()
        logger.info("input artifacts are ready")
        logger.debug(input_artifacts)
        logger.info(f"PYTHON PATH: {os.environ.get('PYTHONPATH')}")

        output_artifacts = self._preprocess_output_artifacts()

        logger.info(f"output_artifacts: {output_artifacts}")
        config = TaskConfigSpec(
            job_id="",
            task_id=self.config.config.task_id,
            party_task_id=f"{self.config.config.task_id}_{self.self_role}",
            component=self.config.runtime.component.name,
            role=self.self_role,
            party_id=self.self_party_id,
            stage=self.stages,
            parameters=self.config.runtime.component.parameter,
            input_artifacts=input_artifacts,
            output_artifacts=output_artifacts,
            conf=self.generate_conf,
            task_name=self.config.runtime.component.name
        )
        logger.debug(config)
        print(config)
        return config

    def run_component(self, config):
        print("start run task")
        task_parameters = config.dict()
        logger.info("start run task")
        os.makedirs(self.task_input_dir, exist_ok=True)
        os.makedirs(self.task_output_dir, exist_ok=True)
        conf_path = os.path.join(self.task_input_dir, "task_parameters.yaml")
        task_result = os.path.join(self.task_output_dir, "task_result.yaml")
        with open(conf_path, "w") as f:
            yaml.dump(task_parameters, f)
        p = self.backend.run(
            provider_name=ProviderName.FATE,
            task_info=self.task_info,
            engine_run={"cores": 4},
            run_parameters=task_parameters,
            output_path=task_result,
            conf_path=conf_path,
            sync=True,
            config_dir=self.task_output_dir, std_dir=self.task_output_dir
        )
        logger.info(f"finish task with code {p.returncode}")
        print(f"finish task with code {p.returncode}")

        if os.path.exists(task_result):
            with open(task_result, "r") as f:
                try:
                    result = json.load(f)
                    output_meta = ComponentOutputMeta.parse_obj(result)
                    if p.returncode != 0:
                        output_meta.status.code = p.returncode
                    logger.debug(output_meta)
                except:
                    raise RuntimeError(f"Task run failed, you can see the task result file for details: {task_result}")
        else:
            output_meta = ComponentOutputMeta(status=ComponentOutputMeta.Status(
                code=ReturnCode.Task.NO_FOUND_RUN_RESULT,
                exceptions=f"No found task output."
            ))
        return output_meta

    def push_output(self, output_meta: ComponentOutputMeta):
        if self.task_end_with_success(output_meta.status.code):
            if not output_meta.io_meta:
                logger.info("No found io meta, pass push")
                return
            for key, datas in output_meta.io_meta.outputs.data.items():
                self._push_data(key, ArtifactOutputSpec(**datas))

            # push model
            for key, models in output_meta.io_meta.outputs.model.items():
                self._push_model(key, ArtifactOutputSpec(**models))

            # push metric
            for key, metrics in output_meta.io_meta.outputs.metric.items():
                self._push_metric(key, ArtifactOutputSpec(**metrics))

    def set_component_desc(self):
        component_ref = self.config.runtime.component.name
        desc_file = os.path.join(self.task_output_dir, "define.yaml")
        module_file_path = sys.modules[FateSubmit.__module__].__file__
        process_cmd = [
            sys.executable,
            module_file_path,
            "component",
            "desc",
            "--name",
            component_ref,
            "--save",
            desc_file
        ]

        p = subprocess.Popen(
            process_cmd,
            env=os.environ
        )
        p.wait()
        if os.path.exists(desc_file):
            with open(desc_file, "r") as fr:
                desc = yaml.safe_load(fr)
                self._component_desc = ComponentSpecV1(**desc)
        else:
            raise RuntimeError("No found description file")

    def _preprocess_output_artifacts(self):
        output_map = {}
        output_artifacts = {}
        if self.config.runtime.component.output:
            for artifacts_type, artifact in self.component_desc.component.output_artifacts.dict().items():
                for key in self.config.runtime.component.output:
                    if key in artifact:
                        uri = f"file://{self.task_output_dir}/{key}"
                        if artifacts_type == "data":
                            address = self.config.runtime.component.output.get(key)
                            uri = f"standalone://{self.data_home}/{address.namespace}/{address.name}"
                        output_artifact = ArtifactOutputApplySpec(
                            uri=uri,
                            type_name=artifact[key]["types"][0]
                        )
                        output_map[key] = artifacts_type
                        output_artifacts[key] = output_artifact
        self._output_map = output_map
        return output_artifacts

    def _preprocess_input_artifacts(self):
        input_artifacts = {}

        os.environ["STANDALONE_DATA_PATH"] = self.data_home

        # only data
        data = self.component_desc.component.input_artifacts.data
        stage = ""
        if self.config.runtime.component.input:
            for name, address in self.config.runtime.component.input.items():
                if name in data:
                    # set stage
                    stage = data[name].stages[0]
                    if self.self_role not in data[name].roles:
                        logger.info(f"role {self.self_role} does not rely on data {name} input")
                        continue
                    path = os.path.join(self.data_home, address.namespace, address.name)
                    os.makedirs(os.path.dirname(path), exist_ok=True)
                    metadata = self.io.s3_to_local(address, path=path)
                    input_artifacts[name] = metadata
        self._set_stage(stage)
        return input_artifacts

    def _set_stage(self, stage):
        self.stages = self.config.runtime.component.parameter.pop("stage", None) or stage or "train"

    def _generate_logger_conf(self):
        level = "DEBUG"
        delay = True
        formatters = None
        return FlowLogger.create(
            task_log_dir=self.task_logs_dir(),
            job_party_log_dir=self.task_logs_dir(self.self_role),
            level=level,
            delay=delay,
            formatters=formatters
        )

    @staticmethod
    def _generate_device():
        return {
            "type": "CPU"
        }

    def _generate_computing_conf(self):
        return StandaloneComputingSpec(
            type=COMPUTING_ENGINE,
            metadata={"computing_id": f"{self.config.config.session_id}{self.self_role}"}
        )

    def _generate_federation_conf(self):
        host, port = self.config.system.transport.split(":")
        return OSXFederationSpec(type="osx", metadata=OSXFederationSpec.MetadataSpec(
            federation_id=self.config.config.session_id,
            parties=self.parties,
            osx_config=OSXFederationSpec.MetadataSpec.OSXConfig(host=host, port=int(port))
        ))

    @staticmethod
    def generate_storage_conf():
        return COMPUTING_ENGINE

    @staticmethod
    def task_end_with_success(code):
        return code == 0

    def _push_data(self, output_key, output_data: ArtifactOutputSpec):
        if output_data.consumed is False:
            return
        logger.info("save data")
        meta = ArtifactInputApplySpec(
            metadata=Metadata(
                metadata=dict(options=dict(partitions=self._partitions))
            ),
            uri=""
        )
        meta.metadata.metadata["schema"] = output_data.metadata.metadata.get("schema", {})
        meta.metadata.source = output_data.metadata.source
        address = self.config.runtime.component.output.get(output_key)
        path = output_data.uri.split("://")[1]
        logger.info(f"start upload {path} to s3")
        logger.info(f"namespace {address.namespace} name {address.name}")
        self.io.upload_to_s3(path, address.name, address.namespace, metadata=meta.metadata.dict())

    def _push_model(self, output_key, output_model: ArtifactOutputSpec):
        address = self.config.runtime.component.output.get(output_key)
        logger.info("save model")
        meta = ArtifactInputApplySpec(
            metadata=Metadata(
                metadata=dict()
            ),
            uri=""
        )
        meta.metadata.model_key = output_model.metadata.model_key
        meta.metadata.source = output_model.metadata.source
        meta.metadata.model_overview = output_model.metadata.model_overview
        meta.metadata.type_name = output_model.metadata.type_name
        self.io.upload_to_s3(output_model.uri.split("://")[1], address.name, address.namespace, metadata=meta.dict())

    def _push_metric(self, output_key, output_metric: ArtifactOutputSpec):
        address = self.config.runtime.component.output.get(output_key)
        logger.info("save metric")
        meta = ArtifactInputApplySpec(
            metadata=Metadata(
                metadata=dict()
            ),
            uri=""
        )
        meta.metadata.source = output_metric.metadata.source
        meta.metadata.type_name = output_metric.metadata.type_name
        self.io.upload_to_s3(output_metric.uri.split("://")[1], address.name, address.namespace, metadata=meta.dict())

    def report_status(self, code):
        if self.task_end_with_success(code):
            resp = self.mlmd.report_task_status(
                task_id=self.config.config.task_id,
                role=self.config.config.self_role,
                status=TaskStatus.SUCCESS
            )
        else:
            resp = self.mlmd.report_task_status(
                task_id=self.config.config.task_id,
                role=self.config.config.self_role,
                status=TaskStatus.FAILED
            )
        self.log_response(resp, req_info="report status")

    @staticmethod
    def log_response(resp, req_info):
        try:
            logger.info(resp.json())
            resp_json = resp.json()
            if resp_json.get("code") != ReturnCode.Base.SUCCESS:
                logging.exception(f"{req_info}: {resp.text}")
        except Exception:
            logger.error(f"{req_info}: {resp.text}")


class DataIo(object):
    def __init__(self, s3_address):
        self.s3_address = s3_address
        self._storage_session = None

    @property
    def storage_session(self):
        if not self._storage_session:
            protocol, host, port, parameters = self.parser_storage_address(self.s3_address)
            from fate_flow.adapter.bfia import engine_storage
            session = engine_storage.session.S3Session(url=f"http://{host}:{port}", **parameters)
            self._storage_session = session
        return self._storage_session

    @staticmethod
    def parser_storage_address(storage_address):
        from urllib.parse import urlparse, parse_qs
        # url = "s3://ip:port?name=xxx&password=xxx"
        parsed_url = urlparse(storage_address)
        protocol = parsed_url.scheme
        host = parsed_url.hostname
        port = parsed_url.port

        ps = parse_qs(parsed_url.query)
        parameters = {}
        for key in ps.keys():
            parameters[key] = ps.get(key, [''])[0]
        return protocol, host, port, parameters

    def s3_to_local(self, address, path):
        table = self.storage_session.get_table(name=address.name, namespace=address.namespace)
        table.download_data_to_local(local_path=path)
        schema = json.loads(table.meta_output()).get("metadata")
        if not schema:
            schema = {}
        logger.debug(json.dumps(schema))
        metadata = Metadata(**schema)
        self._partitions = metadata.metadata.get("options", {}).get("partitions", DEFAULT_OUTPUT_DATA_PARTITIONS)
        meta = ArtifactInputApplySpec(
            metadata=Metadata(
                **schema
            ),
            uri=f"{COMPUTING_ENGINE}:///{address.namespace}/{address.name}"
        )
        from fate.arch._standalone import _TableMetaManager
        _TableMetaManager.add_table_meta(namespace=address.namespace, name=address.name, num_partitions=self._partitions)
        return meta

    def upload_to_s3(self, path, name, namespace, metadata):
        table = self.storage_session.create_table(name, namespace, column_info=[], metadata=metadata)
        table.upload_local_data(path)
