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
from fate_flow.utils.log_utils import getLogger
from fate_flow.components._base import (
    BaseParam,
    ComponentBase,
    ComponentMeta,
    ComponentInputProtocol,
)
from fate_flow.entity.types import ModelStorage
from fate_flow.pipelined_model import mysql_model_storage, redis_model_storage, tencent_cos_model_storage


LOGGER = getLogger()


ModelStorageClassMap = {
    ModelStorage.REDIS.value: redis_model_storage.RedisModelStorage,
    ModelStorage.MYSQL.value: mysql_model_storage.MysqlModelStorage,
    ModelStorage.TENCENT_COS.value: tencent_cos_model_storage.TencentCOSModelStorage,
}


def get_model_storage(parameters):
    model_storage = parameters.get("store_address", {}).get("storage")
    if not model_storage:
        raise TypeError(f"'store_address' is empty.")
    if model_storage not in ModelStorageClassMap:
        raise ValueError(f"Model storage '{model_storage}' is not supported.")
    return ModelStorageClassMap[model_storage]()


model_store_cpn_meta = ComponentMeta("ModelStore")


@model_store_cpn_meta.bind_param
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


@model_store_cpn_meta.bind_runner.on_local
class ModelStore(ComponentBase):
    def _run(self, input_cpn: ComponentInputProtocol):
        parameters = input_cpn.parameters
        model_storage = get_model_storage(parameters)
        model_storage.store(parameters["model_id"], parameters["model_version"],
                            parameters["store_address"], parameters.get("force_update", False))


model_restore_cpn_meta = ComponentMeta("ModelRestore")


@model_restore_cpn_meta.bind_param
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


@model_restore_cpn_meta.bind_runner.on_local
class ModelRestore(ComponentBase):
    def _run(self, input_cpn: ComponentInputProtocol):
        parameters = input_cpn.parameters
        model_storage = get_model_storage(parameters)
        model_storage.restore(parameters["model_id"], parameters["model_version"], parameters["store_address"])
