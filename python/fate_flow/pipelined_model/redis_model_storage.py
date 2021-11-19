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
from copy import deepcopy

import redis

from fate_flow.pipelined_model.pipelined_model import PipelinedModel
from fate_flow.pipelined_model.model_storage_base import ModelStorageBase
from fate_flow.utils.log_utils import getLogger


LOGGER = getLogger()


class RedisModelStorage(ModelStorageBase):
    key_separator = ":"

    def exists(self, model_id: str, model_version: str, store_address: dict):
        store_key = self.store_key(model_id, model_version)
        red = self.get_connection(store_address)

        counts = red.exists(store_key)
        return counts > 0

    def store(self, model_id: str, model_version: str, store_address: dict, force_update: bool = False):
        """
        Store the model from local cache to redis
        :param model_id:
        :param model_version:
        :param store_address:
        :param force_update:
        :return:
        """
        store_key = self.store_key(model_id, model_version)
        if not force_update and self.exists(model_id, model_version, store_address):
            raise FileExistsError(f"The key {store_key} already exists.")

        model = PipelinedModel(model_id, model_version)
        red = self.get_connection(store_address)

        try:
            model.packaging_model()

            with open(model.archive_model_file_path, "rb") as fr:
                res = red.set(store_key, fr.read(), nx=not force_update, ex=store_address.get("ex", None))
            if res is not True:
                if not force_update:
                    raise FileExistsError(f"The key {store_key} already exists.")
                raise TypeError(f"Execute command failed.")
        except Exception as e:
            LOGGER.exception(e)
            raise Exception(f"Store model {model_id} {model_version} to redis failed.")
        else:
            LOGGER.info(f"Store model {model_id} {model_version} to redis successfully."
                        f"Archive path: {model.archive_model_file_path} Key: {store_key}")

    def restore(self, model_id: str, model_version: str, store_address: dict):
        """
        Restore model from redis to local cache
        :param model_id:
        :param model_version:
        :param store_address:
        :return:
        """
        store_key = self.store_key(model_id, model_version)
        model = PipelinedModel(model_id, model_version)
        red = self.get_connection(store_address)

        try:
            archive_data = red.get(name=store_key)
            if not archive_data:
                raise TypeError(f"The key {store_key} does not exists or is empty.")

            with open(model.archive_model_file_path, "wb") as fw:
                fw.write(archive_data)
            model.unpack_model(model.archive_model_file_path)
        except Exception as e:
            LOGGER.exception(e)
            raise Exception(f"Restore model {model_id} {model_version} from redis failed.")
        else:
            LOGGER.info(f"Restore model {model_id} {model_version} from redis successfully. "
                        f"Archive path: {model.archive_model_file_path} Key: {store_key}")

    @staticmethod
    def get_connection(store_address: dict):
        store_address = deepcopy(store_address)
        del store_address['storage']
        store_address.pop('ex', None)
        return redis.Redis(**store_address)
