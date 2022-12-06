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
import inspect
import os
import sys
from functools import wraps

from peewee import Insert
from playhouse.pool import PooledMySQLDatabase

from arch import file_utils, BaseModel, SerializedField, SerializedType
from fate_flow.runtime.runtime_config import RuntimeConfig
from fate_flow.settings import DATABASE, IS_STANDALONE, stat_logger
from fate_flow.utils.log_utils import getLogger
from fate_flow.utils.object_utils import from_dict_hook


LOGGER = getLogger()


class JsonSerializedField(SerializedField):
    def __init__(self, object_hook=from_dict_hook, object_pairs_hook=None, **kwargs):
        super(JsonSerializedField, self).__init__(serialized_type=SerializedType.JSON, object_hook=object_hook,
                                                  object_pairs_hook=object_pairs_hook, **kwargs)


def singleton(cls, *args, **kw):
    instances = {}

    def _singleton():
        key = str(cls) + str(os.getpid())
        if key not in instances:
            instances[key] = cls(*args, **kw)
        return instances[key]

    return _singleton


@singleton
class BaseDataBase:
    def __init__(self):
        database_config = DATABASE.copy()
        db_name = database_config.pop("name")
        if IS_STANDALONE and not bool(int(os.environ.get("FORCE_USE_MYSQL", 0))):
            # sqlite does not support other options
            Insert.on_conflict = lambda self, *args, **kwargs: self.on_conflict_replace()

            from playhouse.apsw_ext import APSWDatabase
            self.database_connection = APSWDatabase(file_utils.get_project_base_directory("fate_sqlite.db"))
            RuntimeConfig.init_config(USE_LOCAL_DATABASE=True)
            stat_logger.info('init sqlite database on standalone mode successfully')
        else:
            self.database_connection = PooledMySQLDatabase(db_name, **database_config)
            stat_logger.info('init mysql database on cluster mode successfully')


class DatabaseLock:
    def __init__(self, lock_name, timeout=10, db=None):
        self.lock_name = lock_name
        self.timeout = int(timeout)
        self.db = db if db else DB

    def lock(self):
        # SQL parameters only support %s format placeholders
        cursor = self.db.execute_sql("SELECT GET_LOCK(%s, %s)", (self.lock_name, self.timeout))
        ret = cursor.fetchone()
        if ret[0] == 0:
            raise Exception(f'acquire mysql lock {self.lock_name} timeout')
        elif ret[0] == 1:
            return True
        else:
            raise Exception(f'failed to acquire lock {self.lock_name}')

    def unlock(self):
        cursor = self.db.execute_sql("SELECT RELEASE_LOCK(%s)", (self.lock_name, ))
        ret = cursor.fetchone()
        if ret[0] == 0:
            raise Exception(f'mysql lock {self.lock_name} was not established by this thread')
        elif ret[0] == 1:
            return True
        else:
            raise Exception(f'mysql lock {self.lock_name} does not exist')

    def __enter__(self):
        if isinstance(self.db, PooledMySQLDatabase):
            self.lock()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if isinstance(self.db, PooledMySQLDatabase):
            self.unlock()

    def __call__(self, func):
        @wraps(func)
        def magic(*args, **kwargs):
            with self:
                return func(*args, **kwargs)
        return magic


DB = BaseDataBase().database_connection
DB.lock = DatabaseLock


def close_connection():
    try:
        if DB:
            DB.close()
    except Exception as e:
        LOGGER.exception(e)


class DataBaseModel(BaseModel):
    class Meta:
        database = DB


@DB.connection_context()
def init_database_tables():
    table_objs = []
    create_failed_list = []
    for obj in [name for name in DataBaseModel.__subclasses__()]:
        table_objs.append(obj)
        LOGGER.info(f"start create table {obj.__name__}")
        try:
            obj.create_table()
            LOGGER.info(f"create table success: {obj.__name__}")
        except Exception as e:
            LOGGER.exception(e)
            create_failed_list.append(obj.__name__)
    if create_failed_list:
        LOGGER.info(f"create tables failed: {create_failed_list}")
        raise Exception(f"create tables failed: {create_failed_list}")


def fill_db_model_object(model_object, human_model_dict):
    for k, v in human_model_dict.items():
        attr_name = 'f_%s' % k
        if hasattr(model_object.__class__, attr_name):
            setattr(model_object, attr_name, v)
    return model_object
