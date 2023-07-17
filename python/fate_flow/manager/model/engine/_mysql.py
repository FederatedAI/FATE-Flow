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
import base64
import io

from copy import deepcopy

from peewee import PeeweeException, CharField, IntegerField, CompositeKey
from playhouse.pool import PooledMySQLDatabase

from fate_flow.db.base_models import LOGGER, BaseModel, LongTextField
from fate_flow.utils.password_utils import decrypt_database_config

DB = PooledMySQLDatabase(None)
SLICE_MAX_SIZE = 1024 * 1024 * 8


class MachineLearningModel(BaseModel):
    f_storage_key = CharField(max_length=100)
    f_content = LongTextField(default='')
    f_slice_index = IntegerField(default=0)

    class Meta:
        database = DB
        db_table = 't_machine_learning_model'
        primary_key = CompositeKey('f_storage_key', 'f_slice_index')


class MysqlModelStorage(object):
    def __init__(self, storage_address, decrypt_key=None):
        self.init_db(storage_address, decrypt_key)

    def exists(self, storage_key: str):
        try:
            with DB.connection_context():
                counts = MachineLearningModel.select().where(
                    MachineLearningModel.f_storage_key == storage_key
                ).count()
            return counts > 0
        except PeeweeException as e:
            # Table doesn't exist
            if e.args and e.args[0] == 1146:
                return False

            raise e
        finally:
            self.close_connection()

    def delete(self, storage_key):
        if not self.exists(storage_key):
            raise FileNotFoundError(f'The model {storage_key} not found in the database.')
        return MachineLearningModel.delete().where(
            MachineLearningModel.f_storage_key == storage_key
        ).execute()

    def store(self, memory_io, storage_key, force_update=True):
        memory_io.seek(0)
        if not force_update and self.exists(storage_key):
            raise FileExistsError(f'The model {storage_key} already exists in the database.')

        try:
            DB.create_tables([MachineLearningModel])
            with DB.connection_context():
                MachineLearningModel.delete().where(
                    MachineLearningModel.f_storage_key == storage_key
                ).execute()

                LOGGER.info(f'Starting store model {storage_key}.')

                slice_index = 0
                while True:
                    content = memory_io.read(SLICE_MAX_SIZE)
                    if not content:
                        break
                    model_in_table = MachineLearningModel()
                    model_in_table.f_storage_key = storage_key
                    model_in_table.f_content = base64.b64encode(content)
                    model_in_table.f_slice_index = slice_index

                    rows = model_in_table.save(force_insert=True)
                    if not rows:
                        raise IndexError(f'Save slice index {slice_index} failed')

                    LOGGER.info(f'Saved slice index {slice_index} of model {storage_key}.')
                    slice_index += 1
        except Exception as e:
            LOGGER.exception(e)
            raise Exception(f'Store model {storage_key} to mysql failed.')
        else:
            LOGGER.info(f'Store model {storage_key} to mysql successfully.')
        finally:
            self.close_connection()

    def read(self, storage_key):
        _io = io.BytesIO()
        if not self.exists(storage_key):
            raise Exception(f'model {storage_key} not exist in the database.')
        try:
            with DB.connection_context():
                models_in_tables = MachineLearningModel.select().where(
                    MachineLearningModel.f_storage_key == storage_key
                ).order_by(MachineLearningModel.f_slice_index)

                for model in models_in_tables:
                    _io.write(base64.b64decode(model.f_content))

        except Exception as e:
            LOGGER.exception(e)
            raise Exception(f'read model {storage_key} from mysql failed.')
        else:
            LOGGER.debug(f'read model from mysql successfully.')
        finally:
            self.close_connection()
        return _io

    @staticmethod
    def init_db(storage_address, decrypt_key):
        _storage_address = deepcopy(storage_address)
        database = _storage_address.pop('name')
        decrypt_database_config(_storage_address, decrypt_key=decrypt_key)
        DB.init(database, **_storage_address)

    @staticmethod
    def close_connection():
        if DB:
            try:
                DB.close()
            except Exception as e:
                LOGGER.exception(e)
