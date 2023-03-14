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
from werkzeug.datastructures import FileStorage

from fate_flow.entity.spec import FileStorageSpec, MysqlStorageSpec, TencentCosStorageSpec
from fate_flow.entity.types import ModelStorageEngine
from fate_flow.manager.model.handel import FileHandle, MysqlHandel, TencentCosHandel
from fate_flow.runtime.system_settings import MODEL_STORE


class PipelinedModel(object):
    engine = MODEL_STORE.get("engine")
    if engine == ModelStorageEngine.FILE:
        handle = FileHandle(engine_address=FileStorageSpec(**MODEL_STORE.get(engine)))
    elif engine == ModelStorageEngine.MYSQL:
        handle = MysqlHandel(engine_address=MysqlStorageSpec(**MODEL_STORE.get(engine)))
    elif engine == ModelStorageEngine.TENCENT_COS:
        handle = TencentCosHandel(engine_address=TencentCosStorageSpec(**MODEL_STORE.get(engine)))
    else:
        raise ValueError(f"Model storage engine {engine} is not supported.")

    @classmethod
    def upload_model(cls, model_file: FileStorage, dir_name: str, file_name: str, model_id, model_version):
        return cls.handle.upload(model_file, dir_name, file_name, model_id, model_version)

    @classmethod
    def download_model(cls, model_id, model_version, dir_name, file_name):
        return cls.handle.download(model_id, model_version, dir_name, file_name)

    @classmethod
    def read_model(cls, job_id, role, party_id, task_name):
        return cls.handle.read(job_id, role, party_id, task_name)
