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

from ruamel import yaml
from werkzeug.datastructures import FileStorage

from fate_flow.entity.code import ReturnCode
from fate_flow.entity.spec import MLModelSpec
from fate_flow.entity.types import ModelFileFormat
from fate_flow.manager.model.model_meta import ModelMeta
from fate_flow.operation.job_saver import JobSaver


class IOHandle(object):
    @property
    def name(self):
        return self._name

    @staticmethod
    def file_key(model_id, model_version, dir_name, file_name):
        return os.path.join(model_id, model_version, dir_name, file_name)

    def download(self, model_id, model_version, dir_name, file_name):
        storage_key = self.file_key(model_id, model_version, dir_name, file_name)
        return self._download(storage_key=storage_key)

    def upload(self, model_file: FileStorage, dir_name, file_name, model_id, model_version):
        storage_key = self.file_key(model_id, model_version, dir_name, file_name)
        model_meta = self._upload(model_file=model_file, storage_key=storage_key)
        self.log_meta(model_meta, storage_key)

    def log_meta(self, model_meta: MLModelSpec, storage_key: str):
        execution_id = model_meta.party.party_task_id
        task = JobSaver.query_task_by_execution_id(execution_id=execution_id)
        job = JobSaver.query_job(job_id=task.f_job_id, role=task.f_role, party_id=task.f_party_id)[0]
        meta_info = {
            "model_id": job.f_model_id,
            "model_version": job.f_model_version,
            "job_id": task.f_job_id,
            "role": task.f_role,
            "party_id": task.f_party_id,
            "task_name": task.f_task_name,
            "storage_engine": self.name,
            "storage_key": storage_key
        }
        ModelMeta.save(**meta_info)

    def meta_info(self, model_meta: MLModelSpec):
        execution_id = model_meta.party.party_task_id
        task = JobSaver.query_task_by_execution_id(execution_id=execution_id)
        job = JobSaver.query_job(job_id=task.f_job_id, role=task.f_role, party_id=task.f_party_id)[0]
        _meta_info = {
            "model_id": job.f_model_id,
            "model_version": job.f_model_version,
            "job_id": task.f_job_id,
            "role": task.f_role,
            "party_id": task.f_party_id,
            "task_name": task.f_task_name,
            "storage_engine": self.name
        }
        return _meta_info

    def read(self, job_id, role, party_id, task_name):
        model_metas = ModelMeta.query(job_id=job_id, role=role, party_id=party_id, task_name=task_name, reverse=True)
        if not model_metas:
            raise ValueError(ReturnCode.Task.NO_FOUND_MODEL_OUTPUT, "No found output model")
        return self._read(model_metas[0].f_storage_key)

    @property
    def _name(self):
        raise NotImplementedError()

    def _upload(self, **kwargs):
        raise NotImplementedError()

    def _download(self, **kwargs):
        raise NotImplementedError()

    def _read(self, storage_key):
        raise NotImplementedError()

    @classmethod
    def read_meta(cls, _tar: tarfile.TarFile) -> MLModelSpec:
        for name in _tar.getnames():
            if name.endswith("yaml"):
                fp = _tar.extractfile(name).read()
                meta = yaml.safe_load(fp)
                return MLModelSpec.parse_obj(meta)

    @classmethod
    def read_model(cls, _tar: tarfile.TarFile):
        model_cache = {}
        model_meta = cls.read_meta(_tar)
        for model in model_meta.party.models:
            if model.file_format == ModelFileFormat.JSON:
                fp = _tar.extractfile(model.name).read()
                model_cache[model.name] = json.loads(fp)
        return model_cache

    @staticmethod
    def update_meta():
        pass


