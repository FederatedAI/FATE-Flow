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
import os.path
import tarfile
import traceback

from flask import send_file
from ruamel import yaml
from werkzeug.datastructures import FileStorage

from fate_flow.db.base_models import BaseModelOperate
from fate_flow.db.db_models import PipelineModelMeta
from fate_flow.entity.spec import MLModelSpec
from fate_flow.settings import (
    CACHE_MODEL_STORE_PATH,
    SOURCE_MODEL_STORE_PATH,
    stat_logger,
)


class PipelinedModel(object):
    def __init__(self, job_id, role, party_id, model_id: str = None, model_version: int = None, store_engine="file"):
        self.job_id = job_id
        self.model_id = model_id
        self.model_version = model_version
        self.role = role
        self.party_id = party_id
        self.handle = self._set_handle(store_engine)
        self.meta_manager = ModelMeta(model_id, model_version, job_id, role, party_id)

    @classmethod
    def _set_handle(cls, handle_type):
        if handle_type == "file":
            return FileHandle()

    def save_output_model(self, task_name, model_name, component, model_file: FileStorage):
        self.handle.write(self.model_id, self.model_version, self.role, self.party_id, task_name, model_name, model_file)
        self.meta_manager.save(task_name=task_name, component=component, model_name=model_name)

    def read_output_model(self, task_name, model_name):
        return self.handle.read(self.model_id, self.model_version, self.role, self.party_id, task_name, model_name)

    def read_model_data(self, task_name):
        model_data = {}
        message = "success"
        try:
            model_metas = self.meta_manager.query(task_name=task_name)
            for model_meta in model_metas:
                model_data[model_meta.f_model_name] = self.handle.read_cache(
                    model_meta.f_model_id, model_meta.f_model_version, model_meta.f_role, model_meta.f_party_id,
                    model_meta.f_task_name, model_meta.f_model_name
                )
        except Exception as e:
            traceback.print_exc()
            stat_logger.exception(e)
            message = str(e)
        return model_data, message


class ModelMeta(BaseModelOperate):
    def __init__(self, model_id, model_version, job_id, role, party_id):
        self.model_id = model_id
        self.model_version = model_version
        self.job_id = job_id
        self.role = role
        self.party_id = party_id

    def save(self, task_name, component, model_name):
        meta_info = {
            "job_id": self.job_id,
            "model_id": self.model_id,
            "model_version": self.model_version,
            "role": self.role,
            "party_id": self.party_id,
            "task_name": task_name,
            "component": component,
            "model_name": model_name
        }
        self._create_entity(PipelineModelMeta, meta_info)

    def query(self, **kwargs):
        return self._query(PipelineModelMeta, job_id=self.job_id, role=self.role, party_id=self.party_id, **kwargs)


class IOHandle:
    def read(self, model_id, model_version, role, party_id, task_name, model_name):
        ...

    def write(self, model_id, model_version, role, party_id, task_name, model_name, model_data):
        ...


class FileHandle(IOHandle):
    def __init__(self):
        self.model_parser = FileModelParser()

    def write(self, model_id, model_version, role, party_id, task_name, model_name, model_file: FileStorage):
        source_path = generate_model_storage_path(model_id, model_version, role, party_id, task_name, model_name)
        os.makedirs(os.path.dirname(source_path), exist_ok=True)
        model_file.save(source_path)
        self.write_cache(model_id, model_version, role, party_id, task_name, model_name, source_path)

    def read(self, model_id, model_version, role, party_id, task_name, model_name):
        model_path = os.path.join(SOURCE_MODEL_STORE_PATH, model_id, model_version, role, party_id, task_name, model_name)
        return send_file(model_path, attachment_filename=model_name, as_attachment=True)

    def write_cache(self, model_id, model_version, role, party_id, task_name, model_name, source_path):
        return self.model_parser.write_cache(model_id, model_version, role, party_id, task_name, model_name, source_path)

    def read_cache(self, model_id, model_version, role, party_id, task_name, model_name):
        return self.model_parser.read_cache(model_id, model_version, role, party_id, task_name, model_name)


class FileModelParser:
    @staticmethod
    def write_cache(model_id, model_version, role, party_id, task_name, model_name, source_path):
        path = generate_model_storage_path(model_id, model_version, role, party_id, task_name, model_name, cache=True)
        os.makedirs(path, exist_ok=True)
        tar = tarfile.open(source_path, "r:")
        tar.extractall(path=path)
        tar.close()

    @staticmethod
    def read_cache(model_id, model_version, role, party_id, task_name, model_name):
        base_path = generate_model_storage_path(model_id, model_version, role, party_id, task_name, model_name, cache=True)
        model_meta = FileModelParser.get_model_meta(base_path)
        model_cache = {}
        for model in model_meta.party.models:
            if model.file_format == "json":
                model_file_name = os.path.join(base_path, model.name)
                if os.path.exists(model_file_name):
                    with open(model_file_name, "r") as f:
                        model_cache[model.name] = json.load(f)
        return model_cache

    @staticmethod
    def get_model_meta(path) -> MLModelSpec:
        for _file in os.listdir(path):
            if _file.endswith("yaml"):
                with open(os.path.join(path, _file), "r") as fp:
                    meta = yaml.safe_load(fp)
                    return MLModelSpec.parse_obj(meta)


def generate_model_storage_path(model_id, model_version, role, party_id, task_name, model_name=None, cache=False):
    if not cache:
        path = os.path.join(SOURCE_MODEL_STORE_PATH, model_id, str(model_version), role, party_id, task_name, model_name)
    else:
        path = os.path.join(CACHE_MODEL_STORE_PATH, model_id, str(model_version), role, party_id, task_name, model_name)
    return path
