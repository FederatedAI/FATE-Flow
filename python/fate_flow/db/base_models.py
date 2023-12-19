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
import operator
import os
from enum import IntEnum
from functools import wraps

import typing

import peewee
from peewee import (
    BigIntegerField,
    CompositeKey,
    Field,
    FloatField,
    IntegerField,
    Metadata,
    Model,
    TextField
)
from playhouse.pool import PooledMySQLDatabase

from fate_flow.hub.flow_hub import FlowHub

from fate_flow.runtime.system_settings import DATABASE
from fate_flow.utils.base_utils import json_dumps, json_loads, date_string_to_timestamp, \
    current_timestamp, timestamp_to_date
from fate_flow.utils.log_utils import getLogger, sql_logger
from fate_flow.utils.object_utils import from_dict_hook

CONTINUOUS_FIELD_TYPE = {IntegerField, FloatField}
AUTO_DATE_TIMESTAMP_FIELD_PREFIX = {
    "create",
    "start",
    "end",
    "update",
    "read_access",
    "write_access",
}


LOGGER = getLogger()


class SerializedType(IntEnum):
    PICKLE = 1
    JSON = 2


class LongTextField(TextField):
    field_type = "LONGTEXT"


class JSONField(LongTextField):
    default_value = {}

    def __init__(self, object_hook=None, object_pairs_hook=None, **kwargs):
        self._object_hook = object_hook
        self._object_pairs_hook = object_pairs_hook
        super().__init__(**kwargs)

    def db_value(self, value):
        if value is None:
            value = self.default_value
        return json_dumps(value)

    def python_value(self, value):
        if not value:
            return self.default_value
        return json_loads(
            value,
            object_hook=self._object_hook,
            object_pairs_hook=self._object_pairs_hook,
        )


class ListField(JSONField):
    default_value = []


class SerializedField(LongTextField):
    def __init__(
        self,
        serialized_type=SerializedType.PICKLE,
        object_hook=None,
        object_pairs_hook=None,
        **kwargs,
    ):
        self._serialized_type = serialized_type
        self._object_hook = object_hook
        self._object_pairs_hook = object_pairs_hook
        super().__init__(**kwargs)

    def db_value(self, value):
        if self._serialized_type == SerializedType.JSON:
            if value is None:
                return None
            return json_dumps(value, with_type=True)
        else:
            raise ValueError(
                f"the serialized type {self._serialized_type} is not supported"
            )

    def python_value(self, value):
        if self._serialized_type == SerializedType.JSON:
            if value is None:
                return {}
            return json_loads(
                value,
                object_hook=self._object_hook,
                object_pairs_hook=self._object_pairs_hook,
            )
        else:
            raise ValueError(
                f"the serialized type {self._serialized_type} is not supported"
            )


def is_continuous_field(cls: typing.Type) -> bool:
    if cls in CONTINUOUS_FIELD_TYPE:
        return True
    for p in cls.__bases__:
        if p in CONTINUOUS_FIELD_TYPE:
            return True
        elif p != Field and p != object:
            if is_continuous_field(p):
                return True
    else:
        return False


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


def auto_date_timestamp_field():
    return {f"{f}_time" for f in AUTO_DATE_TIMESTAMP_FIELD_PREFIX}


def auto_date_timestamp_db_field():
    return {f"f_{f}_time" for f in AUTO_DATE_TIMESTAMP_FIELD_PREFIX}


def remove_field_name_prefix(field_name):
    return field_name[2:] if field_name.startswith("f_") else field_name


@singleton
class BaseDataBase:
    def __init__(self):
        engine_name = DATABASE.get("engine")
        config = DATABASE.get(engine_name)
        decrypt_key = DATABASE.get("decrypt_key")
        self.database_connection = FlowHub.load_database(engine_name, config, decrypt_key)


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


class BaseModel(Model):
    f_create_time = BigIntegerField(null=True)
    f_update_time = BigIntegerField(null=True)

    def to_json(self):
        # This function is obsolete
        return self.to_dict()

    def to_dict(self):
        return self.__dict__["__data__"]

    def to_human_model_dict(self, only_primary_with: list = None):
        model_dict = self.__dict__["__data__"]

        if not only_primary_with:
            return {remove_field_name_prefix(k): v for k, v in model_dict.items()}

        human_model_dict = {}
        for k in self._meta.primary_key.field_names:
            human_model_dict[remove_field_name_prefix(k)] = model_dict[k]
        for k in only_primary_with:
            human_model_dict[k] = model_dict[f"f_{k}"]
        return human_model_dict

    @property
    def meta(self) -> Metadata:
        return self._meta

    @classmethod
    def get_primary_keys_name(cls):
        return (
            cls._meta.primary_key.field_names
            if isinstance(cls._meta.primary_key, CompositeKey)
            else [cls._meta.primary_key.name]
        )

    @classmethod
    def getter_by(cls, attr):
        return operator.attrgetter(attr)(cls)

    @classmethod
    def query(cls, reverse=None, order_by=None, force=False, **kwargs):
        filters = []
        for f_n, f_v in kwargs.items():
            attr_name = "f_%s" % f_n
            if not hasattr(cls, attr_name) or f_v is None:
                continue
            if type(f_v) in {list, set}:
                f_v = list(f_v)
                if is_continuous_field(type(getattr(cls, attr_name))):
                    if len(f_v) == 2:
                        for i, v in enumerate(f_v):
                            if (
                                isinstance(v, str)
                                and f_n in auto_date_timestamp_field()
                            ):
                                # time type: %Y-%m-%d %H:%M:%S
                                f_v[i] = date_string_to_timestamp(v)
                        lt_value = f_v[0]
                        gt_value = f_v[1]
                        if lt_value is not None and gt_value is not None:
                            filters.append(
                                cls.getter_by(attr_name).between(lt_value, gt_value)
                            )
                        elif lt_value is not None:
                            filters.append(
                                operator.attrgetter(attr_name)(cls) >= lt_value
                            )
                        elif gt_value is not None:
                            filters.append(
                                operator.attrgetter(attr_name)(cls) <= gt_value
                            )
                else:
                    filters.append(operator.attrgetter(attr_name)(cls) << f_v)
            else:
                filters.append(operator.attrgetter(attr_name)(cls) == f_v)
        if filters:
            query_records = cls.select().where(*filters)
            if reverse is not None:
                if isinstance(order_by, str) or not order_by:
                    if not order_by or not hasattr(cls, f"f_{order_by}"):
                        order_by = "create_time"
                    query_records = cls.desc(query_records=query_records, reverse=[reverse], order_by=[order_by])
                elif isinstance(order_by, list):
                    if not isinstance(reverse, list) or len(reverse) != len(order_by):
                        raise ValueError(f"reverse need is list and length={len(order_by)}")
                    query_records = cls.desc(query_records=query_records, reverse=reverse, order_by=order_by)
                else:
                    raise ValueError(f"order_by type {type(order_by)} not support")
            return [query_record for query_record in query_records]

        elif force:
            # force query all
            query_records = cls.select()
            return [query_record for query_record in query_records]
        else:
            return []

    @classmethod
    def desc(cls, query_records, order_by: list, reverse: list):
        _filters = list()
        for _k, _ob in enumerate(order_by):
            if reverse[_k] is True:
                _filters.append(cls.getter_by(f"f_{_ob}").desc())
            else:
                _filters.append(cls.getter_by(f"f_{_ob}").asc())
        return query_records.order_by(*tuple(_filters))

    @classmethod
    def insert(cls, __data=None, **insert):
        if isinstance(__data, dict) and __data:
            __data[cls._meta.combined["f_create_time"]] = current_timestamp()
        if insert:
            insert["f_create_time"] = current_timestamp()

        return super().insert(__data, **insert)

    # update and insert will call this method
    @classmethod
    def _normalize_data(cls, data, kwargs):
        normalized = super()._normalize_data(data, kwargs)
        if not normalized:
            return {}

        normalized[cls._meta.combined["f_update_time"]] = current_timestamp()

        for f_n in AUTO_DATE_TIMESTAMP_FIELD_PREFIX:
            if (
                {f"f_{f_n}_time", f"f_{f_n}_date"}.issubset(cls._meta.combined.keys())
                and cls._meta.combined[f"f_{f_n}_time"] in normalized
                and normalized[cls._meta.combined[f"f_{f_n}_time"]] is not None
            ):
                normalized[cls._meta.combined[f"f_{f_n}_date"]] = timestamp_to_date(
                    normalized[cls._meta.combined[f"f_{f_n}_time"]]
                )

        return normalized


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


class BaseModelOperate:
    @classmethod
    @DB.connection_context()
    def _create_entity(cls, entity_model, entity_info: dict) -> object:
        obj = entity_model()
        obj.f_create_time = current_timestamp()
        for k, v in entity_info.items():
            attr_name = 'f_%s' % k
            if hasattr(entity_model, attr_name):
                setattr(obj, attr_name, v)
        try:
            rows = obj.save(force_insert=True)
            if rows != 1:
                raise Exception("Create {} failed".format(entity_model))
            return obj
        except peewee.IntegrityError as e:
            # if e.args[0] == 1062 or (isinstance(e.args[0], str) and "UNIQUE constraint failed" in e.args[0]):
            #     sql_logger(job_id=entity_info.get("job_id", "fate_flow")).warning(e)
            # else:
            #     raise Exception("Create {} failed:\n{}".format(entity_model, e))
            # raise Exception(e)
            pass
        except Exception as e:
            raise Exception("Create {} failed:\n{}".format(entity_model, e))

    @classmethod
    @DB.connection_context()
    def _query(cls, entity_model, force=False, **kwargs):
        return entity_model.query(force=force, **kwargs)

    @classmethod
    @DB.connection_context()
    def _delete(cls, entity_model, **kwargs):
        _kwargs = {}
        filters = []
        for f_k, f_v in kwargs.items():
            attr_name = "f_%s" % f_k
            filters.append(operator.attrgetter(attr_name)(entity_model) == f_v)
        return entity_model.delete().where(*filters).execute() > 0

    @classmethod
    def safe_save(cls, model, defaults, **kwargs):
        entity_model, status = model.get_or_create(
            **kwargs,
            defaults=defaults)
        if status is False:
            for key in defaults:
                setattr(entity_model, key, defaults[key])
            entity_model.save(force_insert=False)
            return "update"
        return "create"

