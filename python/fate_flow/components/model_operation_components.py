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
#
from fate_arch.common import log
from fate_flow.components._base import BaseParam, ComponentBase, ComponentMeta
from fate_flow.entity.types import ModelStorage
from fate_flow.pipelined_model import mysql_model_storage, redis_model_storage

LOGGER = log.getLogger()

ModelStorageClassMap = {
    ModelStorage.REDIS: redis_model_storage.RedisModelStorage,
    ModelStorage.MYSQL: mysql_model_storage.MysqlModelStorage,
}

model_store_cpn_meta = ComponentMeta("ModelStore")


@model_store_cpn_meta.impl_param
class ModelStoreParam(BaseParam):
    def __init__(
        self,
        model_id: str = None,
        model_version: str = None,
        store_address: dict = None,
        force_update: bool = False,
    ):
        self.model_id = model_id
        self.model_version = model_version
        self.store_address = store_address
        self.force_update = force_update

    def check(self):
        return True


@model_store_cpn_meta.impl_runner("local")
class ModelStore(ComponentBase):
    def run(self, component_parameters: dict = None, run_args: dict = None):
        parameters = component_parameters.get("ModelStoreParam", dict)
        model_storage = ModelStorageClassMap.get(
            parameters["store_address"]["storage"]
        )()
        del parameters["store_address"]["storage"]
        model_storage.store(
            model_id=parameters["model_id"],
            model_version=parameters["model_version"],
            store_address=parameters["store_address"],
            force_update=parameters.get("force_update", False),
        )


model_restore_cpn_meta = ComponentMeta("ModelRestore")


@model_restore_cpn_meta.impl_param
class ModelRestoreParam(BaseParam):
    def __init__(
        self,
        model_id: str = None,
        model_version: str = None,
        store_address: dict = None,
    ):
        self.model_id = model_id
        self.model_version = model_version
        self.store_address = store_address

    def check(self):
        return True


@model_restore_cpn_meta.impl_runner("local")
class ModelRestore(ComponentBase):
    def run(self, component_parameters: dict = None, run_args: dict = None):
        parameters = component_parameters.get("ModelRestoreParam", dict)
        model_storage = ModelStorageClassMap.get(
            parameters["store_address"]["storage"]
        )()
        del parameters["store_address"]["storage"]
        model_storage.restore(
            model_id=parameters["model_id"],
            model_version=parameters["model_version"],
            store_address=parameters["store_address"],
        )
