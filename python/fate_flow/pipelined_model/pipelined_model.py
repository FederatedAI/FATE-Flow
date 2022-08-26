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
import base64
import hashlib
import json
import os
import shutil
import typing

from google.protobuf import json_format

from fate_arch.common.base_utils import json_dumps, json_loads

from fate_flow.component_env_utils import provider_utils
from fate_flow.db.db_models import PipelineComponentMeta
from fate_flow.db.runtime_config import RuntimeConfig
from fate_flow.model import (
    Locker, local_cache_required,
    lock, parse_proto_object,
)
from fate_flow.pipelined_model.pipelined_component import PipelinedComponent
from fate_flow.protobuf.python.pipeline_pb2 import Pipeline
from fate_flow.settings import TEMP_DIRECTORY, stat_logger
from fate_flow.utils.job_utils import (
    PIPELINE_COMPONENT_NAME, PIPELINE_MODEL_ALIAS,
    PIPELINE_COMPONENT_MODULE_NAME, PIPELINE_MODEL_NAME,
)
from fate_flow.utils.base_utils import get_fate_flow_directory


class PipelinedModel(Locker):
    def __init__(self, model_id, model_version):
        """
        Support operations on FATE PipelinedModels
        :param model_id: the model id stored at the local party.
        :param model_version: the model version.
        """
        os.makedirs(TEMP_DIRECTORY, exist_ok=True)

        self.role, self.party_id, self._model_id = model_id.split('#', 2)
        self.party_model_id = self.model_id = model_id
        self.model_version = model_version

        self.pipelined_component = PipelinedComponent(role=self.role, party_id=self.party_id,
                                                      model_id=self._model_id, model_version=self.model_version)
        self.model_path = self.pipelined_component.model_path

        super().__init__(self.model_path)

    def save_pipeline_model(self, pipeline_buffer_object, save_define_meta_file=True):
        model_buffers = {
            PIPELINE_MODEL_NAME: (
                type(pipeline_buffer_object).__name__,
                pipeline_buffer_object.SerializeToString(),
                json_format.MessageToDict(pipeline_buffer_object, including_default_value_fields=True),
            ),
        }
        self.save_component_model(PIPELINE_COMPONENT_NAME, PIPELINE_COMPONENT_MODULE_NAME, PIPELINE_MODEL_ALIAS, model_buffers)

        # only update pipeline model file if save_define_meta_file is False
        if save_define_meta_file:
            self.pipelined_component.save_define_meta_from_db_to_file()

    def save_component_model(self, *args, **kwargs):
        component_model = self.create_component_model(*args, **kwargs)
        self.write_component_model(component_model)

    def create_component_model(self, component_name, component_module_name, model_alias,
                               model_buffers: typing.Dict[str, typing.Tuple[str, bytes, dict]],
                               user_specified_run_parameters: dict = None):
        component_model = {"buffer": {}}

        component_model_storage_path = os.path.join(self.pipelined_component.variables_data_path, component_name, model_alias)
        model_proto_index = {}

        for model_name, (proto_index, object_serialized, object_json) in model_buffers.items():
            storage_path = os.path.join(component_model_storage_path, model_name).replace(get_fate_flow_directory(), "")
            component_model["buffer"][storage_path] = (base64.b64encode(object_serialized).decode(), object_json)
            model_proto_index[model_name] = proto_index  # index of model name and proto buffer class name

            stat_logger.info(f"saved {component_name} {model_alias} {model_name} buffer")

        component_model["component_name"] = component_name
        component_model["component_module_name"] = component_module_name
        component_model["model_alias"] = model_alias
        component_model["model_proto_index"] = model_proto_index
        component_model["run_parameters"] = user_specified_run_parameters

        return component_model

    @lock
    def write_component_model(self, component_model):
        for storage_path, (object_serialized_encoded, object_json) in component_model.get("buffer").items():
            storage_path = get_fate_flow_directory() + storage_path
            os.makedirs(os.path.dirname(storage_path), exist_ok=True)

            with open(storage_path, "wb") as fw:
                fw.write(base64.b64decode(object_serialized_encoded.encode()))

            with open(f"{storage_path}.json", "w", encoding="utf8") as fw:
                fw.write(json_dumps(object_json))

        self.pipelined_component.save_define_meta(
            component_model["component_name"], component_model["component_module_name"],
            component_model["model_alias"], component_model["model_proto_index"],
            component_model.get("run_parameters") or {},
        )

        stat_logger.info(f'saved {component_model["component_name"]} {component_model["model_alias"]} successfully')

    @local_cache_required(True)
    def _read_component_model(self, component_name, model_alias):
        component_model_storage_path = os.path.join(self.pipelined_component.variables_data_path, component_name, model_alias)
        model_proto_index = self.get_model_proto_index(component_name=component_name, model_alias=model_alias)

        model_buffers = {}
        for model_name, buffer_name in model_proto_index.items():
            storage_path = os.path.join(component_model_storage_path, model_name)

            with open(storage_path, "rb") as f:
                buffer_object_serialized_string = f.read()

            try:
                with open(f"{storage_path}.json", encoding="utf-8") as f:
                    buffer_object_json_format = json_loads(f.read())
            except FileNotFoundError:
                buffer_object_json_format = ""
                # TODO: should be running in worker
                """
                buffer_object_json_format = json_format.MessageToDict(
                    parse_proto_object(buffer_name, buffer_object_serialized_string),
                    including_default_value_fields=True
                )
                with open(f"{storage_path}.json", "x", encoding="utf-8") as f:
                    f.write(json_dumps(buffer_object_json_format))
                """

            model_buffers[model_name] = (
                buffer_name,
                buffer_object_serialized_string,
                buffer_object_json_format,
            )

        return model_buffers

    # TODO: use different functions instead of passing arguments
    def read_component_model(self, component_name, model_alias=None, parse=True, output_json=False):
        if model_alias is None:
            model_alias = self.get_model_alias(component_name)

        query = self.pipelined_component.get_define_meta_from_db(
            PipelineComponentMeta.f_component_name == component_name,
            PipelineComponentMeta.f_model_alias == model_alias,
        )
        if not query:
            return {}

        _model_buffers = self._read_component_model(component_name, model_alias)

        model_buffers = {}
        for model_name, (
            buffer_name,
            buffer_object_serialized_string,
            buffer_object_json_format,
        ) in _model_buffers.items():
            if output_json:
                model_buffers[model_name] = buffer_object_json_format
            elif parse:
                model_buffers[model_name] = parse_proto_object(buffer_name, buffer_object_serialized_string)
            else:
                model_buffers[model_name] = [
                    buffer_name,
                    base64.b64encode(buffer_object_serialized_string).decode("ascii"),
                ]

        return model_buffers

    # TODO: integration with read_component_model
    @local_cache_required(True)
    def read_pipeline_model(self, parse=True):
        component_model_storage_path = os.path.join(self.pipelined_component.variables_data_path, PIPELINE_COMPONENT_NAME, PIPELINE_MODEL_ALIAS)
        model_proto_index = self.get_model_proto_index(PIPELINE_COMPONENT_NAME, PIPELINE_MODEL_ALIAS)

        model_buffers = {}
        for model_name, buffer_name in model_proto_index.items():
            with open(os.path.join(component_model_storage_path, model_name), "rb") as fr:
                buffer_object_serialized_string = fr.read()

                model_buffers[model_name] = (parse_proto_object(buffer_name, buffer_object_serialized_string, Pipeline) if parse
                                             else [buffer_name, base64.b64encode(buffer_object_serialized_string).decode()])

        return model_buffers[PIPELINE_MODEL_NAME]

    @local_cache_required(True)
    def collect_models(self, in_bytes=False, b64encode=True):
        define_meta = self.pipelined_component.get_define_meta()
        model_buffers = {}

        for component_name in define_meta.get("model_proto", {}).keys():
            for model_alias, model_proto_index in define_meta["model_proto"][component_name].items():
                component_model_storage_path = os.path.join(self.pipelined_component.variables_data_path, component_name, model_alias)

                for model_name, buffer_name in model_proto_index.items():
                    with open(os.path.join(component_model_storage_path, model_name), "rb") as fr:
                        serialized_string = fr.read()

                    if in_bytes:
                        if b64encode:
                            serialized_string = base64.b64encode(serialized_string).decode()

                        model_buffers[f"{component_name}.{model_alias}:{model_name}"] = serialized_string
                    else:
                        model_buffers[model_name] = parse_proto_object(buffer_name, serialized_string)

        return model_buffers

    @staticmethod
    def get_model_migrate_tool():
        return provider_utils.get_provider_class_object(RuntimeConfig.COMPONENT_PROVIDER, "model_migrate", True)

    @staticmethod
    def get_homo_model_convert_tool():
        return provider_utils.get_provider_class_object(RuntimeConfig.COMPONENT_PROVIDER, "homo_model_convert", True)

    def exists(self):
        return self.pipelined_component.exists()

    @local_cache_required(True)
    def packaging_model(self):
        self.gen_model_import_config()

        # self.archive_model_file_path
        shutil.make_archive(self.archive_model_base_path, 'zip', self.model_path)

        with open(self.archive_model_file_path, 'rb') as f:
            hash_ = hashlib.sha256(f.read()).hexdigest()

        stat_logger.info(f'Make model {self.model_id} {self.model_version} archive successfully. '
                         f'path: {self.archive_model_file_path} hash: {hash_}')
        return hash_

    @lock
    def unpack_model(self, archive_file_path: str, force_update: bool = False, hash_: str = None):
        if self.exists() and not force_update:
            raise FileExistsError(f'Model {self.model_id} {self.model_version} local cache already existed.')

        if hash_ is not None:
            with open(archive_file_path, 'rb') as f:
                sha256 = hashlib.sha256(f.read()).hexdigest()

            if hash_ != sha256:
                raise ValueError(f'Model archive hash mismatch. '
                                    f'path: {archive_file_path} expected: {hash_} actual: {sha256}')

        shutil.unpack_archive(archive_file_path, self.model_path, 'zip')

        stat_logger.info(f'Unpack model {self.model_id} {self.model_version} archive successfully. path: {self.model_path}')

    def get_component_define(self, component_name=None):
        component_define = self.pipelined_component.get_define_meta()['component_define']
        if component_name is None:
            return component_define

        return component_define.get(component_name, {})

    def get_model_proto_index(self, component_name=None, model_alias=None):
        model_proto = self.pipelined_component.get_define_meta()['model_proto']
        if component_name is None:
            return model_proto

        model_proto = model_proto.get(component_name, {})
        if model_alias is None:
            return model_proto

        return model_proto.get(model_alias, {})

    def get_model_alias(self, component_name):
        model_proto_index = self.get_model_proto_index(component_name)
        if len(model_proto_index) != 1:
            raise KeyError('Failed to detect "model_alias", please specify it manually.')

        return next(iter(model_proto_index.keys()))

    @property
    def archive_model_base_path(self):
        return os.path.join(TEMP_DIRECTORY, f'{self.party_model_id}_{self.model_version}')

    @property
    def archive_model_file_path(self):
        return f'{self.archive_model_base_path}.zip'

    @local_cache_required(True)
    def calculate_model_file_size(self):
        size = 0
        for root, dirs, files in os.walk(self.model_path):
            size += sum([os.path.getsize(os.path.join(root, name)) for name in files])
        return round(size/1024)

    @local_cache_required(True)
    def gen_model_import_config(self):
        config = {
            'role': self.role,
            'party_id': int(self.party_id),
            'model_id': self._model_id,
            'model_version': self.model_version,
            'file': self.archive_model_file_path,
            'force_update': False,
        }
        with (self.model_path / 'import_model.json').open('w', encoding='utf-8') as f:
            json.dump(config, f, indent=4)
