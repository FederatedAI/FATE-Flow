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
from fate_flow.db.db_models import DB, MachineLearningModelInfo as MLModel
from fate_flow.db.service_registry import ServerRegistry
from fate_flow.components.model_operation import get_model_storage
from fate_flow.pipelined_model.pipelined_model import PipelinedModel
from fate_flow.settings import HOST


class SyncModel:

    def __init__(self, party_model_id, model_version):
        self.pipeline_model = PipelinedModel(party_model_id, model_version)

        self.model_storage_parameters = {
            'model_id': party_model_id,
            'model_version': model_version,
            'store_address': ServerRegistry.MODEL_STORE_ADDRESS,
        }
        self.model_storage = get_model_storage(self.model_storage_parameters)

        self.lock = DB.lock(f'sync_model_{self.pipeline_model.party_model_id}_{self.pipeline_model.model_version}', -1)

    def local_exits(self):
        return self.pipeline_model.exists()

    def remote_exits(self):
        return self.model_storage.exists(**self.component_parameters)

    def _get_model(self):
        return MLModel.get(
            MLModel.f_role == self.pipeline_model.role,
            MLModel.f_party_id == self.pipeline_model.party_id,
            MLModel.f_model_id == self.pipeline_model._model_id,
            MLModel.f_model_version == self.pipeline_model.model_version,
        )

    @DB.connection_context()
    def upload(self, force_update=False):
        with self.lock:
            model = self._get_model()
            hash = self.model_storage.store(force_update=force_update, **self.model_storage_parameters)

            model.f_archive_sha256 = hash
            model.f_archive_from_ip = HOST
            model.save()

            return model

    @DB.connection_context()
    def download(self, force_update=False):
        with self.lock:
            model = self._get_model()

            if model.f_archive_from_ip != HOST:
                self.model_storage.restore(force_update=force_update, hash=model.f_archive_sha256, **self.model_storage_parameters)

            return model
