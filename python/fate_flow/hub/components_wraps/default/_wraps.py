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
import io
import json
import logging
import os.path
import tarfile
import traceback
import uuid

import yaml

from fate_flow.engine.backend import build_backend
from fate_flow.engine.storage import StorageEngine
from fate_flow.entity.spec.dag import PreTaskConfigSpec, DataWarehouseChannelSpec, ComponentIOArtifactsTypeSpec,\
    TaskConfigSpec, ArtifactInputApplySpec, Metadata, RuntimeTaskOutputChannelSpec, \
    ArtifactOutputApplySpec, ModelWarehouseChannelSpec, ArtifactOutputSpec, ComponentOutputMeta

from fate_flow.entity.types import DataframeArtifactType, TableArtifactType, TaskStatus, ComputingEngine

from fate_flow.hub.components_wraps import WrapsABC
from fate_flow.manager.data.data_manager import DataManager
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

    @property
    def task_input_dir(self):
        return job_utils.get_task_directory(**self.task_info, input=True)

    @property
    def task_output_dir(self):
        return job_utils.get_task_directory(**self.task_info, output=True)

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
            logging.exception(e)
        finally:
            self.report_status(code, exceptions)

    def preprocess(self):
        # input
        logging.info(self.config.input_artifacts)
        input_artifacts = self._preprocess_input_artifacts()
        logging.debug(input_artifacts)

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
            conf=self.config.conf,
            task_name=self.config.task_name
        )
        logging.debug(config)
        return config

    def run_component(self, config):
        task_parameters = config.dict()
        logging.info("start run task")
        os.makedirs(self.task_input_dir, exist_ok=True)
        os.makedirs(self.task_output_dir, exist_ok=True)
        task_parameters_file = os.path.join(self.task_input_dir, "task_parameters.yaml")
        task_result = os.path.join(self.task_output_dir, "task_result.yaml")
        with open(task_parameters_file, "w") as f:
            yaml.dump(task_parameters, f)
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
                logging.debug(output_meta)
        else:
            output_meta = ComponentOutputMeta(status=ComponentOutputMeta.status(code=1, exceptions=p.stdout))
        return output_meta

    def push_output(self, output_meta: ComponentOutputMeta):
        if self.task_end_with_success(output_meta.status.code):
            # push output data to server
            if not output_meta.io_meta:
                logging.info("no io meta, pass push")
                return
            for key, datas in output_meta.io_meta.outputs.data.items():
                if isinstance(datas, list):
                    for data in datas:
                        output_data = ArtifactOutputSpec(**data)
                        self._push_data(key, output_data)
                else:
                    output_data = ArtifactOutputSpec(**datas)
                    self._push_data(key, output_data)

            # push model
            for key, models in output_meta.io_meta.outputs.model.items():
                if isinstance(models, list):
                    for model in models:
                        output_model = ArtifactOutputSpec(**model)
                        self._push_model(key, output_model)
                else:
                    output_model = ArtifactOutputSpec(**models)
                    self._push_model(key, output_model)

            # push metric
            for key, metrics in output_meta.io_meta.outputs.metric.items():
                if isinstance(metrics, list):
                    for metric in metrics:
                        output_metric = ArtifactOutputSpec(**metric)
                        self._push_metric(key, output_metric)
                else:
                    output_metric = ArtifactOutputSpec(**metrics)
                    self._push_metric(key, output_metric)
        # self.report_status(output_meta.status.code, output_meta.status.exceptions)

    def _push_data(self, output_key, output_data: ArtifactOutputSpec):
        logging.debug(f"output data: {output_data}")
        namespace = output_data.metadata.namespace
        name = output_data.metadata.name
        if not namespace and not name:
            namespace, name = self._default_output_info()
        logging.info(f"save data tracking to {namespace}, {name}")
        resp = self.mlmd.save_data_tracking(
            execution_id=self.config.party_task_id,
            output_key=output_key,
            meta_data=output_data.metadata.metadata.get("schema", {}),
            uri=output_data.uri,
            namespace=namespace,
            name=name,
            overview=output_data.metadata.data_overview.dict(),
            source=output_data.metadata.source.dict(),
            data_type=output_data.type_name
        )
        logging.info(resp.text)

    def _push_model(self, output_key, output_model: ArtifactOutputSpec):
        logging.info(f"output data: {output_model}")
        logging.info("save model")
        engine, address = DataManager.uri_to_address(output_model.uri)
        if engine == StorageEngine.FILE:
            _path = address.path
            if os.path.exists(_path):
                if os.path.isdir(_path):
                    path = _path
                    meta_path = os.path.join(path, "meta.yaml")
                    with open(meta_path, "w") as fp:
                        yaml.dump(output_model.metadata.dict(), fp)

                else:
                    path = os.path.dirname(_path)
                    meta_path = os.path.join(path, "meta.yaml")
                    with open(meta_path, "w") as fp:
                        yaml.dump(output_model.metadata.dict(), fp)
                # tar and send to server
                _io = io.BytesIO()
                with tarfile.open(fileobj=_io, mode="x:tar") as tar:
                    for _root, _dir, _files in os.walk(path):
                        for _f in _files:
                            full_path = os.path.join(_root, _f)
                            rel_path = os.path.relpath(full_path, path)
                            tar.add(full_path, rel_path)
                _io.seek(0)
                logging.info(output_model.metadata.dict())
                resp = self.mlmd.save_model(
                    model_id=self.config.model_id,
                    model_version=self.config.model_version,
                    execution_id=self.config.party_task_id,
                    output_key=output_key,
                    fp=_io
                )
                logging.info(resp.text)
            else:
                raise ValueError(f"Model path no found: {_path}")
        else:
            raise ValueError(f"Engine {engine} is not supported")

    def _push_metric(self, output_key, output_metric: ArtifactOutputSpec):
        logging.info(f"output metric: {output_metric}")
        logging.info("save metric")
        engine, address = DataManager.uri_to_address(output_metric.uri)
        if engine == StorageEngine.FILE:
            _path = address.path
            if os.path.exists(_path):
                with open(_path, "r") as f:
                    data = json.load(f)
                    resp = self.mlmd.save_metric(
                        execution_id=self.config.party_task_id,
                        data=data
                    )
                    logging.info(resp.text)
            else:
                raise ValueError(f"Metric path no found: {_path}")
        else:
            raise ValueError(f"Engine {engine} is not supported")

    def _default_output_info(self):
        return f"output_data_{self.config.task_id}_{self.config.task_version}", uuid.uuid1().hex

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

        if self.config.input_artifacts.model:
            for _k, _channels in self.config.input_artifacts.model.items():
                input_artifacts[_k] = None
                if isinstance(_channels, list):
                    input_artifacts[_k] = []
                    for _channel in _channels:
                        input_artifacts[_k].append(self._intput_model_artifacts(_channel))
                else:
                    input_artifacts[_k] = self._intput_model_artifacts(_channels)
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
                        _output_artifacts = []
                        for data_type in data.types:
                            _output_artifacts.append(self._output_artifacts(data_type.type_name, data.is_multi, data.name))
                        # todo: multi-type strategy
                        output_artifacts[data.name] = _output_artifacts[0]
        return output_artifacts

    def _output_artifacts(self, type_name, is_multi, name):
        output_artifacts = ArtifactOutputApplySpec(uri="", type_name=type_name)
        if type_name in [DataframeArtifactType.type_name, TableArtifactType.type_name]:
            if self.config.conf.computing.type == ComputingEngine.STANDALONE:
                os.environ["STANDALONE_DATA_PATH"] = STANDALONE_DATA_HOME
                uri = f"{self.config.conf.computing.type}://{STANDALONE_DATA_HOME}/{self.config.task_id}/{uuid.uuid1().hex}"
            else:
                uri = f"{self.config.conf.computing.type}:///{self.config.task_id}/{uuid.uuid1().hex}"
            if is_multi:
                # replace "{index}"
                uri += "_{index}"
        else:
            path = os.path.join(self.task_output_dir, name)
            uri = os.path.join(f"file://{path}", type_name)
            if is_multi:
                uri += "_{index}"
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
        # data reference conversion
        meta = ArtifactInputApplySpec(metadata=Metadata(metadata={}), uri="")
        query_field = {}
        logging.info(channel)
        if isinstance(channel, DataWarehouseChannelSpec):
            # external data reference -> data meta
            if channel.name and channel.namespace:
                query_field = {
                    "namespace": channel.namespace,
                    "name": channel.name
                }
            else:
                query_field = {
                    "job_id": channel.job_id,
                    "role": self.config.role,
                    "party_id": self.config.party_id,
                    "task_name": channel.producer_task,
                    "output_key": channel.output_artifact_key
                }

        elif isinstance(channel, RuntimeTaskOutputChannelSpec):
            # this job output data reference -> data meta
            query_field = {
                "job_id": self.config.job_id,
                "role": self.config.role,
                "party_id": self.config.party_id,
                "task_name": channel.producer_task,
                "output_key": channel.output_artifact_key
            }
        resp = self.mlmd.query_data_meta(**query_field)
        logging.debug(resp.text)
        resp_json = resp.json()
        if resp_json.get("code") != 0:
            raise ValueError(f"Get data artifacts failed: {query_field}, response: {resp.text}")
        resp_data = resp_json.get("data", [])
        if len(resp_data) == 1:
            data = resp_data[0]
            schema = data.get("meta", {})
            meta.metadata.metadata = {"schema": schema}
            meta.metadata.source = data.get("source", {})
            meta.uri = data.get("path")
            return meta
        elif len(resp_data) > 1:
            meta_list = []
            for data in resp_data:
                schema = data.get("meta", {})
                meta.metadata.metadata = {"schema": schema}
                meta.uri = data.get("path")
                meta.metadata.source = data.get("source", {})
                meta.type_name = data.get("data_type")
                meta_list.append(meta)
            return meta_list
        else:
            raise RuntimeError(resp_data)

    def _intput_model_artifacts(self, channel):
        # model reference conversion
        meta = ArtifactInputApplySpec(metadata=Metadata(metadata={}), uri="")
        query_field = {
            "task_name": channel.producer_task,
            "output_key": channel.output_artifact_key,
            "role": self.config.role,
            "party_id": self.config.party_id
        }
        if isinstance(channel, ModelWarehouseChannelSpec):
            # external model reference -> download to local
            if channel.model_id and channel.model_version:
                query_field.update({
                    "model_id": channel.model_id,
                    "model_version": channel.model_version
                })
            else:
                query_field.update({
                    "model_id": self.config.model_id,
                    "model_version": self.config.model_version
                })
        elif isinstance(channel, RuntimeTaskOutputChannelSpec):
            query_field.update({
                "model_id": self.config.model_id,
                "model_version": self.config.model_version
            })

        # this job output data reference -> data meta
        input_model_base = os.path.join(self.task_input_dir, "model")
        os.makedirs(input_model_base, exist_ok=True)
        _io = io.BytesIO()
        resp = self.mlmd.download_model(**query_field)
        _write = False
        for chunk in resp.iter_content(1024):
            if chunk:
                _io.write(chunk)
                _write = True

        if not _write:
            raise RuntimeError(resp.text)

        _io.seek(0)
        model = tarfile.open(fileobj=_io)

        model_meta = {}
        count = 0
        input_model_file = ""
        logging.info(model.getnames())
        for name in model.getnames():
            fp = model.extractfile(name).read()
            if name.endswith("yaml"):
                model_meta = yaml.safe_load(fp)
            else:
                count += 1
                input_model_file = os.path.join(input_model_base, name)
                with open(input_model_file, "wb") as fw:
                    fw.write(fp)
        if count > 1:
            meta.uri = f"file://{input_model_base}"
        else:
            meta.uri = f"file://{input_model_file}"
        meta.metadata = model_meta
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
