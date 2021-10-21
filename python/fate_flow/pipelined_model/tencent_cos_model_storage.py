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

from qcloud_cos import CosConfig, CosS3Client
from qcloud_cos.cos_exception import CosServiceError

from fate_flow.pipelined_model.pipelined_model import PipelinedModel
from fate_flow.pipelined_model.model_storage_base import ModelStorageBase
from fate_flow.utils.log_utils import getLogger

LOGGER = getLogger()


class TencentCOSModelStorage(ModelStorageBase):

    def exists(self, model_id: str, model_version: str, store_address: dict):
        store_key = self.store_key(model_id, model_version) + '.zip'
        cos = self.get_connection(store_address)

        try:
            cos.head_object(
                Bucket=store_address["Bucket"],
                Key=store_key,
            )
        except CosServiceError as e:
            if e.get_error_code() != 'NoSuchResource':
                raise e
            return False
        else:
            return True

    def store(self, model_id: str, model_version: str, store_address: dict, force_update: bool = False):
        """
        Store the model from local cache to cos
        :param model_id:
        :param model_version:
        :param store_address:
        :param force_update:
        :return:
        """
        store_key = self.store_key(model_id, model_version) + '.zip'
        if not force_update and self.exists(model_id, model_version, store_address):
            raise FileExistsError(f"The object {store_key} already exists.")

        model = PipelinedModel(model_id, model_version)
        cos = self.get_connection(store_address)

        try:
            model.packaging_model()

            response = cos.upload_file(
                Bucket=store_address["Bucket"],
                LocalFilePath=model.archive_model_file_path,
                Key=store_key,
                EnableMD5=True,
            )
        except Exception as e:
            LOGGER.exception(e)
            raise Exception(f"Store model {model_id} {model_version} to Tencent COS failed.")
        else:
            LOGGER.info(f"Store model {model_id} {model_version} to Tencent COS successfully. "
                        f"Archive path: {model.archive_model_file_path} Key: {store_key} ETag: {response['ETag']}")

    def restore(self, model_id: str, model_version: str, store_address: dict):
        """
        Restore model from cos to local cache
        :param model_id:
        :param model_version:
        :param store_address:
        :return:
        """
        store_key = self.store_key(model_id, model_version) + '.zip'
        model = PipelinedModel(model_id, model_version)
        cos = self.get_connection(store_address)

        try:
            cos.download_file(
                Bucket=store_address["Bucket"],
                Key=store_key,
                DestFilePath=model.archive_model_file_path,
                EnableCRC=True,
            )

            model.unpack_model(model.archive_model_file_path)
        except Exception as e:
            LOGGER.exception(e)
            raise Exception(f"Restore model {model_id} {model_version} from Tencent COS failed.")
        else:
            LOGGER.info(f"Restore model {model_id} {model_version} from Tencent COS successfully. "
                        f"Archive path: {model.archive_model_file_path} Key: {store_key}")

    @staticmethod
    def get_connection(store_address: dict):
        store_address = deepcopy(store_address)
        del store_address['storage'], store_address['Bucket']
        return CosS3Client(CosConfig(**store_address))
