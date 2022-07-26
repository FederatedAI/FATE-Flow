#
#  Copyright 2022 The FATE Authors. All Rights Reserved.
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
from copy import deepcopy

from peewee import DoesNotExist

from fate_flow.db.db_models import DB, MachineLearningModelInfo as MLModel, PipelineComponentMeta
from fate_flow.db.service_registry import ServerRegistry
from fate_flow.model import model_storage_base, mysql_model_storage, tencent_cos_model_storage
from fate_flow.pipelined_model.pipelined_model import PipelinedModel
from fate_flow.settings import HOST


model_storage_map = {
    'mysql': mysql_model_storage.MysqlModelStorage,
    'tencent_cos': tencent_cos_model_storage.TencentCOSModelStorage,
}

component_storage_map = {
    'mysql': mysql_model_storage.MysqlComponentStorage,
    'tencent_cos': tencent_cos_model_storage.TencentCOSComponentStorage,
}


def get_storage(storage_map: dict) -> tuple(model_storage_base.ModelStorageBase, dict):
    store_address = deepcopy(ServerRegistry.MODEL_STORE_ADDRESS)

    store_type = store_address.pop('storage')
    if store_type not in storage_map:
        raise KeyError(f"Model storage '{store_type}' is not supported.")

    return storage_map[store_type], store_address


class SyncModel:

    def __init__(self, party_model_id, model_version):
        self.pipelined_model = PipelinedModel(party_model_id, model_version)

        storage, storage_address = get_storage(model_storage_map)
        self.model_storage = storage()
        self.model_storage_parameters = {
            'model_id': party_model_id,
            'model_version': model_version,
            'store_address': storage_address,
        }

        self.lock = DB.lock(f'sync_model_{party_model_id}_{model_version}', -1)

    def local_exits(self):
        return self.pipelined_model.exists()

    def remote_exits(self):
        return self.model_storage.exists(**self.model_storage_parameters)

    def db_exits(self):
        try:
            self.get_model()
        except DoesNotExist:
            return False
        else:
            return True

    def get_model(self):
        return MLModel.get(
            MLModel.f_role == self.pipelined_model.role,
            MLModel.f_party_id == self.pipelined_model.party_id,
            MLModel.f_model_id == self.pipelined_model._model_id,
            MLModel.f_model_version == self.pipelined_model.model_version,
        )

    @DB.connection_context()
    def upload(self, force_update=False):
        if self.remote_exits() and not force_update:
            return

        with self.lock:
            model = self.get_model()

            hash_ = self.model_storage.store(force_update=force_update, **self.model_storage_parameters)

            model.f_archive_sha256 = hash_
            model.f_archive_from_ip = HOST
            model.save()

        return model

    @DB.connection_context()
    def download(self, force_update=False):
        if self.local_exits() and not force_update:
            return

        with self.lock:
            model = self.get_model()

            if force_update or model.f_archive_from_ip != HOST:
                self.model_storage.restore(force_update=force_update, hash_=model.f_archive_sha256, **self.model_storage_parameters)

        return model


class SyncComponent:

    def __init__(self, party_model_id, model_version, component_name):
        storage, storage_address = get_storage(model_storage_map)
        self.component_storage = storage(**storage_address)

        self.pipelined_model = PipelinedModel(party_model_id, model_version)
        self.component_name = component_name

        self.lock = DB.lock(f'sync_component_{self.pipelined_model.party_model_id}_'
                            f'{self.pipelined_model.model_version}_{self.component_name}', -1)

    def get_component(self):
        return PipelineComponentMeta.get(
            PipelineComponentMeta.f_role == self.pipelined_model.role,
            PipelineComponentMeta.f_party_id == self.pipelined_model.party_id,
            PipelineComponentMeta.f_model_id == self.pipelined_model._model_id,
            PipelineComponentMeta.f_model_version == self.pipelined_model.model_version,
            PipelineComponentMeta.f_component_name == self.component_name,
        )

    @DB.connection_context()
    def upload(self):
        with self.lock:
            component = self.get_component()

            hash_ = self.component_storage.upload(self.pipelined_model.party_model_id,
                                                  self.pipelined_model.model_version,
                                                  self.component_name)

            component.f_archive_sha256 = hash_
            component.f_archive_from_ip = HOST
            component.save()

        return component

    @DB.connection_context()
    def download(self):
        if not self.pipelined_model.exists():
            self.pipelined_model.create_pipelined_model()

        with self.lock:
            component = self.get_component()

            self.component_storage.download(self.pipelined_model.party_model_id,
                                            self.pipelined_model.model_version,
                                            self.component_name,
                                            component.f_archive_sha256)

        return component
