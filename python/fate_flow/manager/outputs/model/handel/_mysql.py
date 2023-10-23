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
import tarfile

from flask import send_file
from werkzeug.datastructures import FileStorage

from fate_flow.entity.spec.flow import MysqlStorageSpec
from fate_flow.entity.types import ModelStorageEngine
from fate_flow.manager.outputs.model.engine import MysqlModelStorage
from fate_flow.manager.outputs.model.handel import IOHandle


class MysqlHandel(IOHandle):
    def __init__(self, engine_address: MysqlStorageSpec, decrypt_key=None):
        self.engine = MysqlModelStorage(engine_address.dict(), decrypt_key=decrypt_key)

    @property
    def _name(self):
        return ModelStorageEngine.MYSQL

    def _upload(self, model_file: FileStorage, storage_key):
        memory = io.BytesIO()
        model_file.save(memory)
        metas = self.read_meta(self._tar_io(memory))
        self.engine.store(memory, storage_key)
        return metas

    def _download(self, storage_key):
        memory = self.engine.read(storage_key)
        memory.seek(0)
        return send_file(memory, download_name=storage_key, as_attachment=True, mimetype='application/x-tar')

    def _read(self, storage_key, metas):
        memory = self.engine.read(storage_key)
        _tar_io = self._tar_io(memory)
        return self.read_model(_tar_io, metas)

    def _delete(self, storage_key):
        self.engine.delete(storage_key=storage_key)

    def _load(self, file, storage_key):
        with open(file, "rb") as memory:
            memory.seek(0)
            model_meta = self.read_meta(self._tar_io(memory))
            self.engine.store(memory, storage_key)
            return model_meta

    def _save_as(self, storage_key, path):
        memory = self.engine.read(storage_key)
        memory.seek(0)
        with open(path, "wb") as f:
            f.write(memory.read())
        return path

    @staticmethod
    def _tar_io(memory):
        memory.seek(0)
        return tarfile.open(fileobj=memory)
