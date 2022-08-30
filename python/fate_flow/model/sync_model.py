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
from hashlib import sha256
from typing import Tuple

from peewee import DoesNotExist

from fate_flow.db.db_models import (
    DB, PipelineComponentMeta,
    MachineLearningModelInfo as MLModel,
)
from fate_flow.db.service_registry import ServerRegistry
from fate_flow.model import (
    lock, model_storage_base,
    mysql_model_storage, tencent_cos_model_storage,
)
from fate_flow.pipelined_model import Pipelined
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


def get_storage(storage_map: dict) -> Tuple[model_storage_base.ModelStorageBase, dict]:
    store_address = deepcopy(ServerRegistry.MODEL_STORE_ADDRESS)

    store_type = store_address.pop('storage')
    if store_type not in storage_map:
        raise KeyError(f"Model storage '{store_type}' is not supported.")

    return storage_map[store_type], store_address


class SyncModel(Pipelined):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.pipelined_model = PipelinedModel(self.party_model_id, self.model_version)

        storage, storage_address = get_storage(model_storage_map)
        self.model_storage = storage()
        self.model_storage_parameters = {
            'model_id': self.party_model_id,
            'model_version': self.model_version,
            'store_address': storage_address,
        }

        self.lock = DB.lock(
            sha256(
                '_'.join((
                    'sync_model',
                    self.party_model_id,
                    self.model_version,
                )).encode('utf-8')
            ).hexdigest(),
            -1,
        )

    @DB.connection_context()
    def db_exists(self):
        try:
            self.get_model()
        except DoesNotExist:
            return False
        else:
            return True

    def local_exists(self):
        return self.pipelined_model.exists()

    def remote_exists(self):
        return self.model_storage.exists(**self.model_storage_parameters)

    def get_model(self):
        return MLModel.get(
            MLModel.f_role == self.role,
            MLModel.f_party_id == self.party_id,
            MLModel.f_model_id == self.model_id,
            MLModel.f_model_version == self.model_version,
        )

    @DB.connection_context()
    def upload(self, force_update=False):
        if self.remote_exists() and not force_update:
            return

        with self.lock:
            model = self.get_model()

            hash_ = self.model_storage.store(
                force_update=force_update,
                **self.model_storage_parameters,
            )

            model.f_archive_sha256 = hash_
            model.f_archive_from_ip = HOST
            model.save()

        return model

    @DB.connection_context()
    def download(self, force_update=False):
        if self.local_exists() and not force_update:
            return

        with self.lock:
            model = self.get_model()

            self.model_storage.restore(
                force_update=force_update, hash_=model.f_archive_sha256,
                **self.model_storage_parameters,
            )

        return model


class SyncComponent(Pipelined):

    def __init__(self, *, component_name, **kwargs):
        super().__init__(**kwargs)
        self.component_name = component_name

        self.pipelined_model = PipelinedModel(self.party_model_id, self.model_version)

        storage, storage_address = get_storage(component_storage_map)
        self.component_storage = storage(**storage_address)
        self.component_storage_parameters = (
            self.party_model_id,
            self.model_version,
            self.component_name,
        )

        self.query_args = (
            PipelineComponentMeta.f_role == self.role,
            PipelineComponentMeta.f_party_id == self.party_id,
            PipelineComponentMeta.f_model_id == self.model_id,
            PipelineComponentMeta.f_model_version == self.model_version,
            PipelineComponentMeta.f_component_name == self.component_name,
        )

        self.lock = DB.lock(
            sha256(
                '_'.join((
                    'sync_component',
                    self.party_model_id,
                    self.model_version,
                    self.component_name,
                )).encode('utf-8')
            ).hexdigest(),
            -1,
        )

    @DB.connection_context()
    def db_exists(self):
        return PipelineComponentMeta.select().where(*self.query_args).count() > 0

    def local_exists(self):
        return self.pipelined_model.pipelined_component.exists(self.component_name)

    def remote_exists(self):
        with self.component_storage as storage:
            return storage.exists(*self.component_storage_parameters)

    def get_archive_hash(self):
        query = tuple(PipelineComponentMeta.select().where(*self.query_args).group_by(
            PipelineComponentMeta.f_archive_sha256, PipelineComponentMeta.f_archive_from_ip))
        if len(query) != 1:
            raise ValueError(f'The define_meta data of {self.component_name} in database is invalid.')

        return query[0].f_archive_sha256

    def update_archive_hash(self, hash_):
        PipelineComponentMeta.update(
            f_archive_sha256=hash_,
            f_archive_from_ip=HOST,
        ).where(*self.query_args).execute()

    @DB.connection_context()
    @lock
    def upload(self):
        # check the data in database
        self.get_archive_hash()

        with self.component_storage as storage:
            hash_ = storage.upload(*self.component_storage_parameters)

        self.update_archive_hash(hash_)

    @DB.connection_context()
    @lock
    def download(self):
        hash_ = self.get_archive_hash()

        with self.component_storage as storage:
            storage.download(*self.component_storage_parameters, hash_)

    @DB.connection_context()
    @lock
    def copy(self, source_model_version, hash_):
        with self.component_storage as storage:
            storage.copy(*self.component_storage_parameters, source_model_version)

        self.update_archive_hash(hash_)
