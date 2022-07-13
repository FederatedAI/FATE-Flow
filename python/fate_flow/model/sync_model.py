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

from fate_flow.db.db_models import DB
from fate_flow.db.db_models import MachineLearningModelInfo as MLModel
from fate_flow.db.service_registry import ServerRegistry
from fate_flow.model import model_storage_base, mysql_model_storage, redis_model_storage, tencent_cos_model_storage
from fate_flow.pipelined_model.pipelined_model import PipelinedModel
from fate_flow.settings import HOST


model_storages_map = {
    'mysql': mysql_model_storage.MysqlModelStorage,
    'redis': redis_model_storage.RedisModelStorage,
    'tencent_cos': tencent_cos_model_storage.TencentCOSModelStorage,
}

component_storages_map = {
    'tencent_cos': tencent_cos_model_storage.TencentCOSComponentStorage,
}


class SyncModel:

    def __init__(self, party_model_id, model_version):
        store_address = deepcopy(ServerRegistry.MODEL_STORE_ADDRESS)
        store_type = store_address.pop('storage')
        if store_type not in model_storages_map:
            raise ValueError(f"Model storage '{store_type}' is not supported.")

        self.pipeline_model = PipelinedModel(party_model_id, model_version)

        self.model_storage: model_storage_base.ModelStorageBase = model_storages_map[store_type]()
        self.model_storage_parameters = {
            'model_id': party_model_id,
            'model_version': model_version,
            'store_address': store_address,
        }

        self.lock = DB.lock(f'sync_model_{party_model_id}_{model_version}', -1)

    def local_exits(self):
        return self.pipeline_model.exists()

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
            MLModel.f_role == self.pipeline_model.role,
            MLModel.f_party_id == self.pipeline_model.party_id,
            MLModel.f_model_id == self.pipeline_model._model_id,
            MLModel.f_model_version == self.pipeline_model.model_version,
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
        store_type = ServerRegistry.MODEL_STORE_ADDRESS['storage']
        if store_type not in model_storages_map:
            raise ValueError(f"Model storage '{store_type}' is not supported.")

        self.pipeline_model = PipelinedModel(party_model_id, model_version)
        self.component_name = component_name

        self.component_storage: model_storage_base.ComponentStorageBase = model_storages_map[store_type](
            party_model_id, model_version, component_name)

        self.lock = DB.lock(f'sync_component_{self.pipeline_model.party_model_id}_{self.pipeline_model.model_version}_{self.component_name}', -1)
