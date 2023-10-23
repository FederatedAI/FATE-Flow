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

from copy import deepcopy

from fate_flow.db.base_models import LOGGER


class TencentCosStorage(object):
    def __init__(self, storage_address, decrypt_key=None):
        self.Bucket = storage_address.get("Bucket")
        self.client = self.init_client(storage_address)

    def exists(self, storage_key: str):
        from qcloud_cos import CosServiceError

        try:
            self.client.head_object(
                Bucket=self.Bucket,
                Key=storage_key,
            )
        except CosServiceError as e:
            if e.get_error_code() != 'NoSuchResource':
                raise e
            return False
        else:
            return True

    def store(self, memory_io, storage_key, force_update=True):
        memory_io.seek(0)
        if not force_update and self.exists(storage_key):
            raise FileExistsError(f'The model {storage_key} already exists in the Cos.')

        try:
            rt = self.client.put_object(Bucket=self.Bucket, Key=storage_key, Body=memory_io)
        except Exception as e:
            raise Exception(f"Store model {storage_key} to Tencent COS failed: {e}")
        else:
            LOGGER.info(f"Store model {storage_key} to Tencent COS successfully. "
                        f"ETag: {rt['ETag']}")

    def read(self, storage_key):
        _io = io.BytesIO()
        try:
            rt = self.client.get_object(
                Bucket=self.Bucket,
                Key=storage_key
            )
            _io.write(rt.get("Body").get_raw_stream().read())
        except Exception as e:
            LOGGER.exception(e)
            raise Exception(f"Read model {storage_key} from Tencent COS failed: {e}")
        else:
            LOGGER.info(f"Read model {storage_key} from Tencent COS successfully")
            return _io

    def delete(self, storage_key):
        if not self.exists(storage_key):
            raise FileExistsError(f'The model {storage_key} not exist in the Cos.')
        try:
            rt = self.client.delete_bucket(
                Bucket=self.Bucket,
                Key=storage_key
            )
        except Exception as e:
            LOGGER.exception(e)
            raise Exception(f"Delete model {storage_key} from Tencent COS failed: {e}")

    @staticmethod
    def init_client(storage_address):
        from qcloud_cos import CosS3Client, CosConfig
        store_address = deepcopy(storage_address)
        store_address.pop('Bucket')
        return CosS3Client(CosConfig(**store_address))

