#
#  Copyright 2019 The FATE Authors. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the 'License');
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an 'AS IS' BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
from re import I
import sys
from copy import deepcopy

from peewee import (
    BigIntegerField, CharField, CompositeKey,
    IntegerField, PeeweeException, Value,
)
from playhouse.pool import PooledMySQLDatabase

from fate_arch.common.base_utils import (
    current_timestamp, deserialize_b64,
    serialize_b64, timestamp_to_date,
)
from fate_arch.common.conf_utils import decrypt_database_password, decrypt_database_config
from fate_arch.metastore.base_model import LongTextField

from fate_flow.db.db_models import DataBaseModel
from fate_flow.model.model_storage_base import ComponentStorageBase, ModelStorageBase
from fate_flow.pipelined_model.pipelined_model import PipelinedModel
from fate_flow.pipelined_model.pipelined_component import PipelinedComponent
from fate_flow.utils.log_utils import getLogger


LOGGER = getLogger()
DB = PooledMySQLDatabase(None)

SLICE_MAX_SIZE = 1024*1024*8


class MysqlModelStorage(ModelStorageBase):

    def exists(self, model_id: str, model_version: str, store_address: dict):
        self.get_connection(store_address)

        try:
            with DB.connection_context():
                counts = MachineLearningModel.select().where(
                    MachineLearningModel.f_model_id == model_id,
                    MachineLearningModel.f_model_version == model_version,
                ).count()
            return counts > 0
        except PeeweeException as e:
            # Table doesn't exist
            if e.args and e.args[0] == 1146:
                return False

            raise e
        finally:
            self.close_connection()

    def store(self, model_id: str, model_version: str, store_address: dict, force_update: bool = False):
        '''
        Store the model from local cache to mysql
        :param model_id:
        :param model_version:
        :param store_address:
        :param force_update:
        :return:
        '''
        if not force_update and self.exists(model_id, model_version, store_address):
            raise FileExistsError(f'The model {model_id} {model_version} already exists in the database.')

        try:
            self.get_connection(store_address)
            DB.create_tables([MachineLearningModel])

            model = PipelinedModel(model_id, model_version)
            hash_ = model.packaging_model()

            with open(model.archive_model_file_path, 'rb') as fr, DB.connection_context():
                MachineLearningModel.delete().where(
                    MachineLearningModel.f_model_id == model_id,
                    MachineLearningModel.f_model_version == model_version,
                ).execute()

                LOGGER.info(f'Starting store model {model_id} {model_version}.')

                slice_index = 0
                while True:
                    content = fr.read(SLICE_MAX_SIZE)
                    if not content:
                        break

                    model_in_table = MachineLearningModel()
                    model_in_table.f_model_id = model_id
                    model_in_table.f_model_version = model_version
                    model_in_table.f_content = serialize_b64(content, to_str=True)
                    model_in_table.f_size = sys.getsizeof(model_in_table.f_content)
                    model_in_table.f_slice_index = slice_index

                    rows = model_in_table.save(force_insert=True)
                    if not rows:
                        raise IndexError(f'Save slice index {slice_index} failed')

                    LOGGER.info(f'Saved slice index {slice_index} of model {model_id} {model_version}.')
                    slice_index += 1
        except Exception as e:
            LOGGER.exception(e)
            raise Exception(f'Store model {model_id} {model_version} to mysql failed.')
        else:
            LOGGER.info(f'Store model {model_id} {model_version} to mysql successfully.')
            return hash_
        finally:
            self.close_connection()

    def restore(self, model_id: str, model_version: str, store_address: dict, force_update: bool = False, hash_: str = None):
        '''
        Restore model from mysql to local cache
        :param model_id:
        :param model_version:
        :param store_address:
        :return:
        '''
        model = PipelinedModel(model_id, model_version)
        self.get_connection(store_address)

        try:
            with DB.connection_context():
                models_in_tables = MachineLearningModel.select().where(
                    MachineLearningModel.f_model_id == model_id,
                    MachineLearningModel.f_model_version == model_version,
                ).order_by(MachineLearningModel.f_slice_index)

            with open(model.archive_model_file_path, 'wb') as fw:
                for models_in_table in models_in_tables:
                    fw.write(deserialize_b64(models_in_table.f_content))

                if fw.tell() == 0:
                    raise IndexError(f'Cannot found model in table.')

            model.unpack_model(model.archive_model_file_path, force_update, hash_)
        except Exception as e:
            LOGGER.exception(e)
            raise Exception(f'Restore model {model_id} {model_version} from mysql failed.')
        else:
            LOGGER.info(f'Restore model to {model.archive_model_file_path} from mysql successfully.')
        finally:
            self.close_connection()

    @staticmethod
    def get_connection(store_address: dict):
        store_address = deepcopy(store_address)
        store_address.pop('storage', None)
        database = store_address.pop('database')

        store_address = decrypt_database_config(store_address, 'password')
        DB.init(database, **store_address)

    @staticmethod
    def close_connection():
        if DB:
            try:
                DB.close()
            except Exception as e:
                LOGGER.exception(e)


class MysqlComponentStorage(ComponentStorageBase):

    def __init__(self, database, user, password, host, port, **connect_kwargs):
        self.database = database
        self.user = user
        self.password = decrypt_database_password(password)
        self.host = host
        self.port = port
        self.connect_kwargs = connect_kwargs

    def __enter__(self):
        DB.init(self.database, user=self.user, password=self.password, host=self.host, port=self.port, **self.connect_kwargs)

        return self

    def __exit__(self, *exc):
        DB.close()

    def exists(self, party_model_id, model_version, component_name):
        try:
            with DB.connection_context():
                counts = MachineLearningComponent.select().where(
                    MachineLearningComponent.f_party_model_id == party_model_id,
                    MachineLearningComponent.f_model_version == model_version,
                    MachineLearningComponent.f_component_name == component_name,
                ).count()
            return counts > 0
        except PeeweeException as e:
            # Table doesn't exist
            if e.args and e.args[0] == 1146:
                return False

            raise e

    def upload(self, party_model_id, model_version, component_name):
        DB.create_tables([MachineLearningComponent])

        pipelined_component = PipelinedComponent(party_model_id=party_model_id, model_version=model_version)
        filename, hash_ = pipelined_component.pack_component(component_name)

        with open(filename, 'rb') as fr, DB.connection_context():
            MachineLearningComponent.delete().where(
                MachineLearningComponent.f_party_model_id == party_model_id,
                MachineLearningComponent.f_model_version == model_version,
                MachineLearningComponent.f_component_name == component_name,
            ).execute()

            slice_index = 0
            while True:
                content = fr.read(SLICE_MAX_SIZE)
                if not content:
                    break

                model_in_table = MachineLearningComponent()
                model_in_table.f_party_model_id = party_model_id
                model_in_table.f_model_version = model_version
                model_in_table.f_component_name = component_name
                model_in_table.f_content = serialize_b64(content, to_str=True)
                model_in_table.f_size = sys.getsizeof(model_in_table.f_content)
                model_in_table.f_slice_index = slice_index

                rows = model_in_table.save(force_insert=True)
                if not rows:
                    raise IndexError(f'Save slice index {slice_index} failed')

                slice_index += 1

        return hash_

    def download(self, party_model_id, model_version, component_name, hash_=None):
        with DB.connection_context():
            models_in_tables = MachineLearningComponent.select().where(
                MachineLearningComponent.f_party_model_id == party_model_id,
                MachineLearningComponent.f_model_version == model_version,
                MachineLearningComponent.f_component_name == component_name,
            ).order_by(MachineLearningComponent.f_slice_index)

        pipelined_component = PipelinedComponent(party_model_id=party_model_id, model_version=model_version)

        with open(pipelined_component.get_archive_path(component_name), 'wb') as fw:
            for models_in_table in models_in_tables:
                fw.write(deserialize_b64(models_in_table.f_content))

            if fw.tell() == 0:
                raise IndexError(f'Cannot found component model in table.')

        pipelined_component.unpack_component(component_name, hash_)

    @DB.connection_context()
    def copy(self, party_model_id, model_version, component_name, source_model_version):
        now = current_timestamp()

        source = MachineLearningComponent.select(
            MachineLearningComponent.f_create_time,
            MachineLearningComponent.f_create_date,
            Value(now).alias('f_update_time'),
            Value(timestamp_to_date(now)).alias('f_update_date'),

            MachineLearningComponent.f_party_model_id,
            Value(model_version).alias('f_model_version'),
            MachineLearningComponent.f_component_name,

            MachineLearningComponent.f_size,
            MachineLearningComponent.f_content,
            MachineLearningComponent.f_slice_index,
        ).where(
            MachineLearningComponent.f_party_model_id == party_model_id,
            MachineLearningComponent.f_model_version == source_model_version,
            MachineLearningComponent.f_component_name == component_name,
        ).order_by(MachineLearningComponent.f_slice_index)

        rows = MachineLearningComponent.insert_from(source, (
            MachineLearningComponent.f_create_time,
            MachineLearningComponent.f_create_date,
            MachineLearningComponent.f_update_time,
            MachineLearningComponent.f_update_date,

            MachineLearningComponent.f_party_model_id,
            MachineLearningComponent.f_model_version,
            MachineLearningComponent.f_component_name,

            MachineLearningComponent.f_size,
            MachineLearningComponent.f_content,
            MachineLearningComponent.f_slice_index,
        )).execute()

        if not rows:
            raise IndexError(f'Copy component model failed.')


class MachineLearningModel(DataBaseModel):
    f_model_id = CharField(max_length=100, index=True)
    f_model_version = CharField(max_length=100, index=True)
    f_size = BigIntegerField(default=0)
    f_content = LongTextField(default='')
    f_slice_index = IntegerField(default=0, index=True)

    class Meta:
        db_table = 't_machine_learning_model'
        primary_key = CompositeKey('f_model_id', 'f_model_version', 'f_slice_index')


class MachineLearningComponent(DataBaseModel):
    f_party_model_id = CharField(max_length=100, index=True)
    f_model_version = CharField(max_length=100, index=True)
    f_component_name = CharField(max_length=100, index=True)
    f_size = BigIntegerField(default=0)
    f_content = LongTextField(default='')
    f_slice_index = IntegerField(default=0, index=True)

    class Meta:
        db_table = 't_machine_learning_component'
        indexes = (
            (('f_party_model_id', 'f_model_version', 'f_component_name', 'f_slice_index'), True),
        )
