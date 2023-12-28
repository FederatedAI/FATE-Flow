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
import os
import shutil
from tempfile import TemporaryDirectory

from werkzeug.datastructures import FileStorage

from fate_flow.entity.spec.flow import FileStorageSpec, MysqlStorageSpec, TencentCosStorageSpec
from fate_flow.entity.types import ModelStorageEngine
from fate_flow.manager.outputs.model.handel import FileHandle, MysqlHandel, TencentCosHandel
from fate_flow.manager.outputs.model.model_meta import ModelMeta
from fate_flow.runtime.system_settings import MODEL_STORE
from fate_flow.errors.server_error import NoFoundModelOutput


class PipelinedModel(object):
    engine = MODEL_STORE.get("engine")
    decrypt_key = MODEL_STORE.get("decrypt_key")
    if engine == ModelStorageEngine.FILE:
        handle = FileHandle(engine_address=FileStorageSpec(**MODEL_STORE.get(engine)))
    elif engine == ModelStorageEngine.MYSQL:
        handle = MysqlHandel(engine_address=MysqlStorageSpec(**MODEL_STORE.get(engine)), decrypt_key=decrypt_key)
    elif engine == ModelStorageEngine.TENCENT_COS:
        handle = TencentCosHandel(engine_address=TencentCosStorageSpec(**MODEL_STORE.get(engine)),
                                  decrypt_key=decrypt_key)
    else:
        raise ValueError(f"Model storage engine {engine} is not supported.")

    @classmethod
    def upload_model(cls, model_file: FileStorage, job_id: str, task_name, output_key, model_id, model_version, role,
                     party_id, type_name):
        return cls.handle.upload(model_file, job_id, task_name, output_key, model_id, model_version, role,
                                 party_id, type_name)

    @classmethod
    def download_model(cls, **kwargs):
        return cls.handle.download(**kwargs)

    @classmethod
    def read_model(cls, job_id, role, party_id, task_name):
        return cls.handle.read(job_id, role, party_id, task_name)

    @classmethod
    def delete_model(cls, **kwargs):
        return cls.handle.delete(**kwargs)

    @classmethod
    def export_model(cls, model_id, model_version, role, party_id, dir_path):
        _key_list = cls.get_model_storage_key(model_id=model_id, model_version=model_version, role=role, party_id=party_id)
        if not _key_list:
            raise NoFoundModelOutput(model_id=model_id, model_version=model_version, role=role, party_id=party_id)
        with TemporaryDirectory() as temp_dir:
            for _k in _key_list:
                temp_path = os.path.join(temp_dir, _k)
                cls.handle.save_as(storage_key=_k, temp_path=temp_path)
            os.makedirs(dir_path, exist_ok=True)
            shutil.make_archive(os.path.join(dir_path, f"{model_id}_{model_version}_{role}_{party_id}"), 'zip', temp_dir)

    @classmethod
    def import_model(cls, model_id, model_version, path, temp_dir):
        base_dir = os.path.dirname(path)
        shutil.unpack_archive(path, base_dir, 'zip')
        for dirpath, dirnames, filenames in os.walk(base_dir):
            for filename in filenames:
                model_path = os.path.join(dirpath, filename)
                # exclude original model packs
                if model_path != path:
                    _storage_key = model_path.lstrip(f"{temp_dir}{os.sep}")
                    _, _, role, party_id, task_name, output_key = cls.handle.parse_storage_key(_storage_key)
                    storage_key = cls.handle.storage_key(model_id, model_version, role, party_id, task_name, output_key)
                    cls.handle.load(model_path, storage_key, model_id, model_version, role=role, party_id=party_id,
                                    task_name=task_name, output_key=output_key)

    @classmethod
    def get_model_storage_key(cls, **kwargs):
        _key_list = []
        _model_metas = ModelMeta.query(**kwargs)
        for _meta in _model_metas:
            _key_list.append(_meta.f_storage_key)
        return _key_list
