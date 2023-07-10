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
from typing import Union, List

import yaml

from fate_flow.engine.backend import build_backend
from fate_flow.engine.storage import StorageEngine
from fate_flow.entity.code import ReturnCode
from fate_flow.entity.spec.dag import PreTaskConfigSpec, DataWarehouseChannelSpec, ComponentIOArtifactsTypeSpec, \
    TaskConfigSpec, ArtifactInputApplySpec, Metadata, RuntimeTaskOutputChannelSpec, \
    ArtifactOutputApplySpec, ModelWarehouseChannelSpec, ArtifactOutputSpec, ComponentOutputMeta, TaskCleanupConfigSpec

from fate_flow.entity.types import DataframeArtifactType, TableArtifactType, TaskStatus, ComputingEngine, \
    JsonModelArtifactType

from fate_flow.hub.components_wraps import WrapsABC
from fate_flow.manager.data.data_manager import DataManager
from fate_flow.runtime.system_settings import STANDALONE_DATA_HOME, DEFAULT_OUTPUT_DATA_PARTITIONS
from fate_flow.utils import job_utils


class FlowWraps(WrapsABC):
    def __init__(self, config: PreTaskConfigSpec):
        self.config = config
        self.mlmd = self.load_mlmd(config.mlmd)
        self.backend = build_backend(backend_name=self.config.conf.computing.type)
        self._component_define = None

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
            code = output_meta.status.code
            exceptions = None
            if output_meta.status.code != ReturnCode.Base.SUCCESS:
                code = ReturnCode.Task.COMPONENT_RUN_FAILED
                exceptions = output_meta.status.exceptions
                logging.exception(exceptions)
        except Exception as e:
            traceback.format_exc()
            code = ReturnCode.Task.TASK_RUN_FAILED
            exceptions = str(e)
            logging.exception(e)
        finally:
            self.report_status(code, exceptions)

    def cleanup(self):
        config = TaskCleanupConfigSpec(
            computing=self.config.conf.computing,
            federation=self.config.conf.federation
        )
        return self.backend.cleanup(
            provider_name=self.config.provider_name,
            config=config.dict(),
            task_info=self.task_info
        )

    def preprocess(self):
        # input
        logging.info("start generating input artifacts")
        logging.info(self.config.input_artifacts)
        input_artifacts = self._preprocess_input_artifacts()
        logging.info("success")
        logging.debug(input_artifacts)
        logging.info(f"PYTHON PATH: {os.environ.get('PYTHONPATH')}")

        # output
        logging.info("start generating output artifacts")
        output_artifacts = self._preprocess_output_artifacts()
        logging.info(f"output_artifacts: {output_artifacts}")
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
        self._set_env()
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
                try:
                    result = json.load(f)
                    output_meta = ComponentOutputMeta.parse_obj(result)
                    logging.debug(output_meta)
                except:
                    logging.exception(f"Task run failed, you can see the task result file for details: {task_result}")
        else:
            output_meta = ComponentOutputMeta(status=ComponentOutputMeta.Status(
                code=ReturnCode.Task.NO_FOUND_RUN_RESULT,
                exceptions=f"Task output no found, process output stderr: {p.stderr}"
            ))
        return output_meta

    def push_output(self, output_meta: ComponentOutputMeta):
        if self.task_end_with_success(output_meta.status.code):
            # push output data to server
            if not output_meta.io_meta:
                logging.info("No found io meta, pass push")
                return
            for key, datas in output_meta.io_meta.outputs.data.items():
                if isinstance(datas, list):
                    self._push_data(key, [ArtifactOutputSpec(**data) for data in datas])
                else:
                    self._push_data(key, [ArtifactOutputSpec(**datas)])

            # push model
            for key, models in output_meta.io_meta.outputs.model.items():
                if isinstance(models, list):
                    self._push_model(key, [ArtifactOutputSpec(**model) for model in models])
                else:
                    self._push_model(key, [ArtifactOutputSpec(**models)])

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

    def _push_data(self, output_key, output_datas: List[ArtifactOutputSpec]):
        logging.info("save data")
        logging.info(f"key[{output_key}] output_datas[{output_datas}]")
        for index, output_data in enumerate(output_datas):
            namespace = output_data.metadata.namespace
            name = output_data.metadata.name
            if not namespace and not name:
                namespace, name = self._default_output_info()
            logging.info(f"save data tracking to {namespace}, {name}")
            overview = output_data.metadata.data_overview
            source = output_data.metadata.source
            resp = self.mlmd.save_data_tracking(
                execution_id=self.config.party_task_id,
                output_key=output_key,
                meta_data=output_data.metadata.metadata.get("schema", {}),
                uri=output_data.uri,
                namespace=namespace,
                name=name,
                overview=overview.dict() if overview else {},
                source=source.dict() if source else {},
                data_type=output_data.type_name,
                index=index,
                partitions=DEFAULT_OUTPUT_DATA_PARTITIONS
            )
            logging.info(resp.text)

    def _push_model(self, output_key, output_models: List[ArtifactOutputSpec]):
        logging.info("save model")
        logging.info(f"key[{output_key}] output_models[{output_models}]")
        tar_io = io.BytesIO()
        for output_model in output_models:
            engine, address = DataManager.uri_to_address(output_model.uri)
            if engine == StorageEngine.FILE:
                _path = address.path
                if os.path.exists(_path):
                    if os.path.isdir(_path):
                        path = _path
                    else:
                        path = os.path.dirname(_path)
                    model_key = os.path.basename(_path)
                    meta_path = os.path.join(path, f"{model_key}.meta.yaml")
                    with open(meta_path, "w") as fp:
                        output_model.metadata.model_key = model_key
                        output_model.metadata.index = output_model.metadata.source.output_index
                        output_model.metadata.type_name = output_model.type_name
                        yaml.dump(output_model.metadata.dict(), fp)
                    # tar and send to server
                    tar_io = self._tar_model(tar_io=tar_io, path=path)
                    type_name = output_model.type_name
                else:
                    logging.warning(f"Model path no found: {_path}")
            else:
                raise ValueError(f"Engine {engine} is not supported")

        resp = self.mlmd.save_model(
            model_id=self.config.model_id,
            model_version=self.config.model_version,
            execution_id=self.config.party_task_id,
            output_key=output_key,
            fp=tar_io,
            type_name=type_name
        )
        logging.info(resp.text)

    @staticmethod
    def _tar_model(tar_io, path):
        with tarfile.open(fileobj=tar_io, mode="x:tar") as tar:
            for _root, _dir, _files in os.walk(path):
                for _f in _files:
                    full_path = os.path.join(_root, _f)
                    rel_path = os.path.relpath(full_path, path)
                    tar.add(full_path, rel_path)
        tar_io.seek(0)
        return tar_io

    def _push_metric(self, output_key, output_metric: ArtifactOutputSpec):
        logging.info(f"output metric: {output_metric}")
        logging.info("save metric")
        engine, address = DataManager.uri_to_address(output_metric.uri)
        if engine == StorageEngine.FILE:
            _path = address.path
            if os.path.exists(_path):
                with open(_path, "r") as f:
                    data = json.load(f)
                    if data:
                        resp = self.mlmd.save_metric(
                            execution_id=self.config.party_task_id,
                            data=data
                        )
                        logging.info(resp.text)
            else:
                logging.warning(f"Metric path no found: {_path}")
        else:
            raise ValueError(f"Engine {engine} is not supported")

    def _default_output_info(self):
        return f"output_data_{self.config.task_id}_{self.config.task_version}", uuid.uuid1().hex

    def _preprocess_input_artifacts(self):
        input_artifacts = {}
        if self.config.input_artifacts.data:
            for _k, _channels in self.config.input_artifacts.data.items():
                if isinstance(_channels, list):
                    input_artifacts[_k] = []
                    for _channel in _channels:
                        _artifacts = self._intput_data_artifacts(_k, _channel)
                        if _artifacts:
                            input_artifacts[_k].append(_artifacts)
                else:
                    input_artifacts[_k] = self._intput_data_artifacts(_k, _channels)
                if not input_artifacts[_k]:
                    input_artifacts.pop(_k)

        if self.config.input_artifacts.model:
            for _k, _channels in self.config.input_artifacts.model.items():
                if isinstance(_channels, list):
                    input_artifacts[_k] = []
                    for _channel in _channels:
                        input_artifacts[_k].append(self._intput_model_artifacts(_k, _channel))
                else:
                    input_artifacts[_k] = self._intput_model_artifacts(_k, _channels)
                if not input_artifacts[_k]:
                    input_artifacts.pop(_k)
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

    def _set_env(self):
        if self.config.conf.computing.type == ComputingEngine.STANDALONE or \
                self.config.conf.federation.type == ComputingEngine.STANDALONE:
            os.environ["STANDALONE_DATA_PATH"] = STANDALONE_DATA_HOME

    def _output_artifacts(self, type_name, is_multi, name):
        output_artifacts = ArtifactOutputApplySpec(uri="", type_name=type_name)
        if type_name in [DataframeArtifactType.type_name, TableArtifactType.type_name]:
            if self.config.conf.computing.type == ComputingEngine.STANDALONE:
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
    def component_define(self) -> ComponentIOArtifactsTypeSpec:
        if not self._component_define:
            self.set_component_define()
        return self._component_define

    def set_component_define(self):
        define = self.backend.get_component_define(
            provider_name=self.config.provider_name,
            task_info=self.task_info,
            stage=self.config.stage
        )
        if define:
            self._component_define = ComponentIOArtifactsTypeSpec(**define)

    def _intput_data_artifacts(self, key, channel):
        if self.config.role not in channel.roles:
            logging.info(f"role {self.config.role} does not require intput data artifacts")
            return
        # data reference conversion
        meta = ArtifactInputApplySpec(metadata=Metadata(metadata={}), uri="")
        query_field = {}
        logging.info(f"get key[{key}] channel[{channel}]")
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
        logging.info(f"query data: [{query_field}]")
        resp = self.mlmd.query_data_meta(**query_field)
        logging.debug(resp.text)
        resp_json = resp.json()
        if resp_json.get("code") != 0:
            # Judging whether to optional
            for input_data_define in self.component_define.inputs.data:
                if input_data_define.name == key and input_data_define.optional:
                    logging.info(f"component define input data name {key} optional {input_data_define.optional}")
                    return
            raise ValueError(f"Get data artifacts failed: {query_field}, response: {resp.text}")
        resp_data = resp_json.get("data", [])
        logging.info(f"success")
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

    def _intput_model_artifacts(self, key, channel):
        if self.config.role not in channel.roles:
            logging.info(f"role {self.config.role} does not require intput model artifacts")
            return
        # model reference conversion
        meta = ArtifactInputApplySpec(metadata=Metadata(metadata={}), uri="")
        query_field = {
            "task_name": channel.producer_task,
            "output_key": channel.output_artifact_key,
            "role": self.config.role,
            "party_id": self.config.party_id
        }
        logging.info(f"get key[{key}] channel[{channel}]")
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

        logging.info(f"query model: [{query_field}]")

        # this job output data reference -> data meta
        input_model_base = os.path.join(self.task_input_dir, "model")
        os.makedirs(input_model_base, exist_ok=True)
        _io = io.BytesIO()
        resp = self.mlmd.download_model(**query_field)
        if resp.headers.get('content-type') == 'application/json':
            raise RuntimeError(f"Download model failed, {resp.text}")
        try:
            for chunk in resp.iter_content(1024):
                if chunk:
                    _io.write(chunk)
            _io.seek(0)
            model = tarfile.open(fileobj=_io)
        except Exception as e:
            for input_data_define in self.component_define.inputs.model:
                if input_data_define.name == key and input_data_define.optional:
                    logging.info(f"component define input model name {key} optional {input_data_define.optional}")
                    return
            raise RuntimeError(f"Download model failed: {query_field}")
        logging.info(f"get model channel success, model names: {model.getnames()}")
        metas = []
        file_names = model.getnames()
        for name in file_names:
            if name.endswith("yaml"):
                fp = model.extractfile(name).read()
                model_meta = yaml.safe_load(fp)
                model_meta = Metadata.parse_obj(model_meta)
                model_key = model_meta.model_key
                input_model_file = os.path.join(input_model_base, model_key)
                if model_meta.type_name not in [JsonModelArtifactType.type_name]:
                    self._write_model_dir(model, input_model_file)
                else:
                    model_fp = model.extractfile(model_key).read()
                    with open(input_model_file, "wb") as fw:
                        fw.write(model_fp)
                meta.uri = f"file://{input_model_file}"
                meta.metadata = model_meta
                metas.append(meta)
        if not metas:
            raise RuntimeError(f"Download model failed: {query_field}")
        if len(metas) == 1:
            return metas[0]
        return metas

    @staticmethod
    def _write_model_dir(model, path):
        for name in model.getnames():
            if not name.endswith("yaml"):
                model_fp = model.extractfile(name).read()
                input_model_file = os.path.join(path, name)
                os.makedirs(os.path.dirname(input_model_file), exist_ok=True)
                with open(input_model_file, "wb") as fw:
                    fw.write(model_fp)

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
