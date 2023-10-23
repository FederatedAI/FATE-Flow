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
import os.path
import shutil
import tarfile

from flask import send_file
from werkzeug.datastructures import FileStorage

from fate_flow.entity.spec.flow import FileStorageSpec
from fate_flow.entity.types import ModelStorageEngine
from fate_flow.manager.outputs.model.handel import IOHandle
from fate_flow.runtime.system_settings import MODEL_STORE_PATH


class FileHandle(IOHandle):
    def __init__(self, engine_address: FileStorageSpec):
        self.path = engine_address.path if engine_address.path else MODEL_STORE_PATH

    @property
    def _name(self):
        return ModelStorageEngine.FILE

    def _upload(self, model_file: FileStorage, storage_key):
        _path = self._generate_model_storage_path(storage_key)
        os.makedirs(os.path.dirname(_path), exist_ok=True)
        model_file.save(_path)
        model_metas = self.read_meta(self._tar_io(_path))
        return model_metas

    def _download(self, storage_key):
        _p = self._generate_model_storage_path(storage_key)
        return send_file(_p, download_name=os.path.basename(_p), as_attachment=True, mimetype='application/x-tar')

    def _save_as(self, storage_key, path):
        _p = self._generate_model_storage_path(storage_key)
        shutil.copy(_p, path)
        return path

    def _load(self, file, storage_key):
        _path = self._generate_model_storage_path(storage_key)
        os.makedirs(os.path.dirname(_path), exist_ok=True)
        shutil.copy(file, _path)
        return self.read_meta(self._tar_io(_path))

    def _read(self, storage_key, metas):
        _p = self._generate_model_storage_path(storage_key)
        _tar_io = self._tar_io(_p)
        return self.read_model(_tar_io, metas)

    def _delete(self, storage_key):
        _p = self._generate_model_storage_path(storage_key)
        return os.remove(_p)

    @staticmethod
    def _tar_io(path):
        with open(path, "rb") as f:
            return tarfile.open(fileobj=io.BytesIO(f.read()))

    def _generate_model_storage_path(self, storage_key):
        return os.path.join(self.path, storage_key)
