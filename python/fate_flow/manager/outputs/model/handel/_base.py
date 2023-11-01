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
from typing import Union, List

from ruamel import yaml
from werkzeug.datastructures import FileStorage

from fate_flow.entity.spec.flow import Metadata
from fate_flow.errors.server_error import NoFoundModelOutput
from fate_flow.manager.outputs.model.model_meta import ModelMeta
from fate_flow.manager.operation.job_saver import JobSaver


class IOHandle(object):
    @property
    def name(self):
        return self._name

    @staticmethod
    def storage_key(model_id, model_version, role, party_id, task_name, output_key):
        return os.path.join(model_id, model_version, role, party_id, task_name, output_key)

    @staticmethod
    def parse_storage_key(storage_key):
        return storage_key.split(os.sep)

    def download(self, job_id=None, model_id=None, model_version=None, role=None, party_id=None, task_name=None,
                 output_key=None):
        model_metas = ModelMeta.query(model_id=model_id, model_version=model_version, task_name=task_name,
                                      output_key=output_key, role=role, party_id=party_id, job_id=job_id)
        if not model_metas:
            raise ValueError("No found model")
        return self._download(storage_key=model_metas[0].f_storage_key)

    def upload(self, model_file: FileStorage, job_id, task_name, output_key, model_id, model_version, role,
               party_id, type_name):
        storage_key = self.storage_key(model_id, model_version, role, party_id, task_name, output_key)
        metas = self._upload(model_file=model_file, storage_key=storage_key)
        self.log_meta(metas,  storage_key, job_id=job_id, task_name=task_name, model_id=model_id, type_name=type_name,
                      model_version=model_version, output_key=output_key, role=role, party_id=party_id)

    def save_as(self, storage_key, temp_path):
        os.makedirs(os.path.dirname(temp_path), exist_ok=True)
        return self._save_as(storage_key, temp_path)

    def load(self, file, storage_key, model_id, model_version, role, party_id, task_name, output_key):
        metas = self._load(file=file, storage_key=storage_key)
        self.log_meta(metas, storage_key, model_id=model_id, model_version=model_version, role=role, party_id=party_id,
                      task_name=task_name, output_key=output_key)

    def delete(self, **kwargs):
        model_metas = ModelMeta.query(storage_engine=self.name, **kwargs)
        if not model_metas:
            raise NoFoundModelOutput(**kwargs)
        for meta in model_metas:
            try:
                self._delete(storage_key=meta.f_storage_key)
            except:
                pass
        return self.delete_meta(storage_engine=self.name, **kwargs)

    def log_meta(self, model_metas, storage_key, model_id, model_version, output_key, task_name, role, party_id,
                 job_id="", type_name=""):
        model_info = {
            "storage_key": storage_key,
            "storage_engine": self.name,
            "model_id": model_id,
            "model_version": model_version,
            "job_id": job_id,
            "role": role,
            "party_id": party_id,
            "task_name": task_name,
            "output_key": output_key,
            "meta_data": model_metas,
            "type_name": type_name
        }
        ModelMeta.save(**model_info)

    @staticmethod
    def delete_meta(**kwargs):
        return ModelMeta.delete(**kwargs)

    def meta_info(self, model_meta: Metadata):
        execution_id = model_meta.model_overview.party.party_task_id
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
        models = ModelMeta.query(job_id=job_id, role=role, party_id=party_id, task_name=task_name, reverse=True)
        if not models:
            raise NoFoundModelOutput(job_id=job_id, role=role, party_id=party_id, task_name=task_name)
        model_dict = {}
        for model in models:
            model_dict[model.f_output_key] = self._read(model.f_storage_key, model.f_meta_data)
        return model_dict

    @property
    def _name(self):
        raise NotImplementedError()

    def _upload(self, **kwargs):
        raise NotImplementedError()

    def _download(self, **kwargs):
        raise NotImplementedError()

    def _read(self, storage_key, metas):
        raise NotImplementedError()

    def _delete(self, storage_key):
        raise NotImplementedError()

    def _save_as(self, storage_key, path):
        raise NotImplementedError()

    def _load(self, file, storage_key):
        raise NotImplementedError()

    @classmethod
    def read_meta(cls, _tar: tarfile.TarFile) -> Union[Metadata, List[Metadata]]:
        meta_list = []
        for name in _tar.getnames():
            if name.endswith("yaml"):
                fp = _tar.extractfile(name).read()
                meta = yaml.safe_load(fp)
                meta_list.append(meta)
        return meta_list

    @classmethod
    def read_model(cls, _tar: tarfile.TarFile, metas):
        model_cache = {}
        for _meta in metas:
            meta = Metadata(**_meta)
            try:
                fp = _tar.extractfile(meta.model_key).read()
                _json_model = json.loads(fp)
                if meta.index is None:
                    return _json_model
                model_cache[meta.index] = _json_model
            except Exception as e:
                pass
        return [model_cache[_k] for _k in sorted(model_cache)]

    @staticmethod
    def update_meta():
        pass


