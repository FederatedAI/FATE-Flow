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
import datetime
import inspect
import os
import sys

from peewee import (CharField, IntegerField, BigIntegerField,
                    TextField, CompositeKey, BigAutoField, BooleanField)
from playhouse.pool import PooledMySQLDatabase

from fate_arch.common import file_utils
from fate_flow.utils.log_utils import getLogger
from fate_arch.metastore.base_model import JSONField, BaseModel, LongTextField, DateTimeField, SerializedField, \
    SerializedType, ListField
from fate_flow.db.runtime_config import RuntimeConfig
from fate_flow.settings import DATABASE, stat_logger, IS_STANDALONE
from fate_flow.utils.object_utils import from_dict_hook


LOGGER = getLogger()


class JsonSerializedField(SerializedField):
    def __init__(self, object_hook=from_dict_hook, object_pairs_hook=None, **kwargs):
        super(JsonSerializedField, self).__init__(serialized_type=SerializedType.JSON, object_hook=object_hook, object_pairs_hook=object_pairs_hook, **kwargs)


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
        if IS_STANDALONE:
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
        self.timeout = timeout
        self.db = db if db else DB

    def lock(self):
        sql = "SELECT GET_LOCK('%s', %s)" % (self.lock_name, self.timeout)
        cursor = self.db.execute_sql(sql)
        ret = cursor.fetchone()
        if ret[0] == 0:
            raise Exception('mysql lock {} is already used'.format(self.lock_name))
        elif ret[0] == 1:
            return True
        else:
            raise Exception('mysql lock {} error occurred!')

    def unlock(self):
        sql = "SELECT RELEASE_LOCK('%s')" % (self.lock_name)
        cursor = self.db.execute_sql(sql)
        ret = cursor.fetchone()
        if ret[0] == 0:
            raise Exception('mysql lock {} is not released'.format(self.lock_name))
        elif ret[0] == 1:
            return True
        else:
            raise Exception('mysql lock {} did not exist.'.format(self.lock_name))

    def __enter__(self):
        if isinstance(self.db, PooledMySQLDatabase):
            self.lock()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if isinstance(self.db, PooledMySQLDatabase):
            self.unlock()


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
    members = inspect.getmembers(sys.modules[__name__], inspect.isclass)
    table_objs = []
    create_failed_list = []
    for name, obj in members:
        if obj != DataBaseModel and issubclass(obj, DataBaseModel):
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


class Job(DataBaseModel):
    # multi-party common configuration
    f_user_id = CharField(max_length=25, null=True)
    f_job_id = CharField(max_length=25, index=True)
    f_name = CharField(max_length=500, null=True, default='')
    f_description = TextField(null=True, default='')
    f_tag = CharField(max_length=50, null=True, default='')
    f_dsl = JSONField()
    f_runtime_conf = JSONField()
    f_runtime_conf_on_party = JSONField()
    f_train_runtime_conf = JSONField(null=True)
    f_roles = JSONField()
    f_initiator_role = CharField(max_length=50)
    f_initiator_party_id = CharField(max_length=50)
    f_status = CharField(max_length=50)
    f_status_code = IntegerField(null=True)
    f_user = JSONField()
    # this party configuration
    f_role = CharField(max_length=50, index=True)
    f_party_id = CharField(max_length=10, index=True)
    f_is_initiator = BooleanField(null=True, default=False)
    f_progress = IntegerField(null=True, default=0)
    f_ready_signal = BooleanField(default=False)
    f_ready_time = BigIntegerField(null=True)
    f_cancel_signal = BooleanField(default=False)
    f_cancel_time = BigIntegerField(null=True)
    f_rerun_signal = BooleanField(default=False)
    f_end_scheduling_updates = IntegerField(null=True, default=0)

    f_engine_name = CharField(max_length=50, null=True)
    f_engine_type = CharField(max_length=10, null=True)
    f_cores = IntegerField(default=0)
    f_memory = IntegerField(default=0)  # MB
    f_remaining_cores = IntegerField(default=0)
    f_remaining_memory = IntegerField(default=0)  # MB
    f_resource_in_use = BooleanField(default=False)
    f_apply_resource_time = BigIntegerField(null=True)
    f_return_resource_time = BigIntegerField(null=True)

    f_inheritance_info = JSONField(null=True)
    f_inheritance_status = CharField(max_length=50, null=True)

    f_start_time = BigIntegerField(null=True)
    f_start_date = DateTimeField(null=True)
    f_end_time = BigIntegerField(null=True)
    f_end_date = DateTimeField(null=True)
    f_elapsed = BigIntegerField(null=True)

    class Meta:
        db_table = "t_job"
        primary_key = CompositeKey('f_job_id', 'f_role', 'f_party_id')


class Task(DataBaseModel):
    # multi-party common configuration
    f_job_id = CharField(max_length=25, index=True)
    f_component_name = TextField()
    f_component_module = CharField(max_length=200)
    f_task_id = CharField(max_length=100)
    f_task_version = BigIntegerField()
    f_initiator_role = CharField(max_length=50)
    f_initiator_party_id = CharField(max_length=50, default=-1)
    f_federated_mode = CharField(max_length=10)
    f_federated_status_collect_type = CharField(max_length=10)
    f_status = CharField(max_length=50, index=True)
    f_status_code = IntegerField(null=True)
    f_auto_retries = IntegerField(default=0)
    f_auto_retry_delay = IntegerField(default=0)
    # this party configuration
    f_role = CharField(max_length=50, index=True)
    f_party_id = CharField(max_length=10, index=True)
    f_run_on_this_party = BooleanField(null=True, index=True, default=False)
    f_worker_id = CharField(null=True, max_length=100)
    f_cmd = JSONField(null=True)
    f_run_ip = CharField(max_length=100, null=True)
    f_run_pid = IntegerField(null=True)
    f_party_status = CharField(max_length=50)
    f_provider_info = JSONField()
    f_component_parameters = JSONField()
    f_engine_conf = JSONField(null=True)

    f_start_time = BigIntegerField(null=True)
    f_start_date = DateTimeField(null=True)
    f_end_time = BigIntegerField(null=True)
    f_end_date = DateTimeField(null=True)
    f_elapsed = BigIntegerField(null=True)

    class Meta:
        db_table = "t_task"
        primary_key = CompositeKey('f_job_id', 'f_task_id', 'f_task_version', 'f_role', 'f_party_id')


class TrackingMetric(DataBaseModel):
    _mapper = {}

    @classmethod
    def model(cls, table_index=None, date=None):
        if not table_index:
            table_index = date.strftime(
                '%Y%m%d') if date else datetime.datetime.now().strftime(
                '%Y%m%d')
        class_name = 'TrackingMetric_%s' % table_index

        ModelClass = TrackingMetric._mapper.get(class_name, None)
        if ModelClass is None:
            class Meta:
                db_table = '%s_%s' % ('t_tracking_metric', table_index)

            attrs = {'__module__': cls.__module__, 'Meta': Meta}
            ModelClass = type("%s_%s" % (cls.__name__, table_index), (cls,),
                              attrs)
            TrackingMetric._mapper[class_name] = ModelClass
        return ModelClass()

    f_id = BigAutoField(primary_key=True)
    f_job_id = CharField(max_length=25, index=True)
    f_component_name = TextField()
    f_task_id = CharField(max_length=100, null=True, index=True)
    f_task_version = BigIntegerField(null=True, index=True)
    f_role = CharField(max_length=50, index=True)
    f_party_id = CharField(max_length=10, index=True)
    f_metric_namespace = CharField(max_length=180)
    f_metric_name = CharField(max_length=180)
    f_key = CharField(max_length=200)
    f_value = LongTextField()
    f_type = IntegerField()  # 0 is data, 1 is meta


class TrackingOutputDataInfo(DataBaseModel):
    _mapper = {}

    @classmethod
    def model(cls, table_index=None, date=None):
        if not table_index:
            table_index = date.strftime(
                '%Y%m%d') if date else datetime.datetime.now().strftime(
                '%Y%m%d')
        class_name = 'TrackingOutputDataInfo_%s' % table_index

        ModelClass = TrackingOutputDataInfo._mapper.get(class_name, None)
        if ModelClass is None:
            class Meta:
                db_table = '%s_%s' % ('t_tracking_output_data_info', table_index)
                primary_key = CompositeKey('f_job_id', 'f_task_id', 'f_task_version', 'f_data_name', 'f_role', 'f_party_id')

            attrs = {'__module__': cls.__module__, 'Meta': Meta}
            ModelClass = type("%s_%s" % (cls.__name__, table_index), (cls,),
                              attrs)
            TrackingOutputDataInfo._mapper[class_name] = ModelClass
        return ModelClass()

    # multi-party common configuration
    f_job_id = CharField(max_length=25, index=True)
    f_component_name = TextField()
    f_task_id = CharField(max_length=100, null=True, index=True)
    f_task_version = BigIntegerField(null=True)
    f_data_name = CharField(max_length=30)
    # this party configuration
    f_role = CharField(max_length=50, index=True)
    f_party_id = CharField(max_length=10, index=True)
    f_table_name = CharField(max_length=500, null=True)
    f_table_namespace = CharField(max_length=500, null=True)
    f_description = TextField(null=True, default='')


class MachineLearningModelInfo(DataBaseModel):
    f_role = CharField(max_length=50)
    f_party_id = CharField(max_length=10)
    f_roles = JSONField(default={})
    f_job_id = CharField(max_length=25, index=True)
    f_model_id = CharField(max_length=100, index=True)
    f_model_version = CharField(max_length=100, index=True)
    f_loaded_times = IntegerField(default=0)
    f_size = BigIntegerField(default=0)
    f_description = TextField(null=True, default='')
    f_initiator_role = CharField(max_length=50)
    f_initiator_party_id = CharField(max_length=50, default=-1)
    f_runtime_conf = JSONField(default={})
    f_train_dsl = JSONField(default={})
    f_train_runtime_conf = JSONField(default={})
    f_imported = IntegerField(default=0)
    f_job_status = CharField(max_length=50, null=True)
    f_runtime_conf_on_party = JSONField(default={})
    f_fate_version = CharField(max_length=10, null=True, default='')
    f_parent = BooleanField(null=True, default=None)
    f_parent_info = JSONField(default={})
    f_inference_dsl = JSONField(default={})

    class Meta:
        db_table = "t_machine_learning_model_info"
        primary_key = CompositeKey('f_role', 'f_party_id', 'f_model_id', 'f_model_version')


class DataTableTracking(DataBaseModel):
    f_table_id = BigAutoField(primary_key=True)
    f_table_name = CharField(max_length=300, null=True)
    f_table_namespace = CharField(max_length=300, null=True)
    f_job_id = CharField(max_length=25, index=True, null=True)
    f_have_parent = BooleanField(default=False)
    f_parent_number = IntegerField(default=0)

    f_parent_table_name = CharField(max_length=500, null=True)
    f_parent_table_namespace = CharField(max_length=500, null=True)
    f_source_table_name = CharField(max_length=500, null=True)
    f_source_table_namespace = CharField(max_length=500, null=True)

    class Meta:
        db_table = "t_data_table_tracking"


class CacheRecord(DataBaseModel):
    f_cache_key = CharField(max_length=500)
    f_cache = JsonSerializedField()
    f_job_id = CharField(max_length=25, index=True, null=True)
    f_role = CharField(max_length=50, index=True, null=True)
    f_party_id = CharField(max_length=10, index=True, null=True)
    f_component_name = TextField(null=True)
    f_task_id = CharField(max_length=100, null=True)
    f_task_version = BigIntegerField(null=True, index=True)
    f_cache_name = CharField(max_length=50, null=True)
    t_ttl = BigIntegerField(default=0)

    class Meta:
        db_table = "t_cache_record"


class ModelTag(DataBaseModel):
    f_id = BigAutoField(primary_key=True)
    f_m_id = CharField(max_length=25, null=False)
    f_t_id = BigIntegerField(null=False)

    class Meta:
        db_table = "t_model_tag"


class Tag(DataBaseModel):
    f_id = BigAutoField(primary_key=True)
    f_name = CharField(max_length=100, unique=True)
    f_desc = TextField(null=True)

    class Meta:
        db_table = "t_tags"


class ComponentSummary(DataBaseModel):
    _mapper = {}

    @classmethod
    def model(cls, table_index=None, date=None):
        if not table_index:
            table_index = date.strftime(
                '%Y%m%d') if date else datetime.datetime.now().strftime(
                '%Y%m%d')
        class_name = 'ComponentSummary_%s' % table_index

        ModelClass = TrackingMetric._mapper.get(class_name, None)
        if ModelClass is None:
            class Meta:
                db_table = '%s_%s' % ('t_component_summary', table_index)

            attrs = {'__module__': cls.__module__, 'Meta': Meta}
            ModelClass = type("%s_%s" % (cls.__name__, table_index), (cls,), attrs)
            ComponentSummary._mapper[class_name] = ModelClass
        return ModelClass()

    f_id = BigAutoField(primary_key=True)
    f_job_id = CharField(max_length=25, index=True)
    f_role = CharField(max_length=25, index=True)
    f_party_id = CharField(max_length=10, index=True)
    f_component_name = TextField()
    f_task_id = CharField(max_length=50, null=True, index=True)
    f_task_version = CharField(max_length=50, null=True)
    f_summary = LongTextField()


class ModelOperationLog(DataBaseModel):
    f_operation_type = CharField(max_length=20, null=False, index=True)
    f_operation_status = CharField(max_length=20, null=True, index=True)
    f_initiator_role = CharField(max_length=50, index=True, null=True)
    f_initiator_party_id = CharField(max_length=10, index=True, null=True)
    f_request_ip = CharField(max_length=20, null=True)
    f_model_id = CharField(max_length=100)
    f_model_version = CharField(max_length=100)

    class Meta:
        db_table = "t_model_operation_log"


class EngineRegistry(DataBaseModel):
    f_engine_type = CharField(max_length=10, index=True)
    f_engine_name = CharField(max_length=50, index=True)
    f_engine_entrance = CharField(max_length=50, index=True)
    f_engine_config = JSONField()
    f_cores = IntegerField()
    f_memory = IntegerField()  # MB
    f_remaining_cores = IntegerField()
    f_remaining_memory = IntegerField() # MB
    f_nodes = IntegerField()

    class Meta:
        db_table = "t_engine_registry"
        primary_key = CompositeKey('f_engine_name', 'f_engine_type')


# component registry
class ComponentRegistryInfo(DataBaseModel):
    f_provider_name = CharField(max_length=20, index=True)
    f_version = CharField(max_length=10, index=True)
    f_component_name = CharField(max_length=30, index=True)
    f_module = CharField(max_length=128)

    class Meta:
        db_table = "t_component_registry"
        primary_key = CompositeKey('f_provider_name', 'f_version', 'f_component_name')


class ComponentProviderInfo(DataBaseModel):
    f_provider_name = CharField(max_length=20, index=True)
    f_version = CharField(max_length=10, index=True)
    f_class_path = JSONField()
    f_path = CharField(max_length=128, null=False)
    f_python = CharField(max_length=128, null=False)

    class Meta:
        db_table = "t_component_provider_info"
        primary_key = CompositeKey('f_provider_name', 'f_version')


class ComponentInfo(DataBaseModel):
    f_component_name = CharField(max_length=30, primary_key=True)
    f_component_alias = JSONField()
    f_default_provider = CharField(max_length=20)
    f_support_provider = ListField(null=True)

    class Meta:
        db_table = "t_component_info"


class WorkerInfo(DataBaseModel):
    f_worker_id = CharField(max_length=100, primary_key=True)
    f_worker_name = CharField(max_length=50, index=True)
    f_job_id = CharField(max_length=25, index=True)
    f_task_id = CharField(max_length=100)
    f_task_version = BigIntegerField(index=True)
    f_role = CharField(max_length=50)
    f_party_id = CharField(max_length=10, index=True)
    f_run_ip = CharField(max_length=100, null=True)
    f_run_pid = IntegerField(null=True)
    f_http_port = IntegerField(null=True)
    f_grpc_port = IntegerField(null=True)
    f_config = JSONField(null=True)
    f_cmd = JSONField(null=True)
    f_start_time = BigIntegerField(null=True)
    f_start_date = DateTimeField(null=True)
    f_end_time = BigIntegerField(null=True)
    f_end_date = DateTimeField(null=True)

    class Meta:
        db_table = "t_worker"


class DependenciesStorageMeta(DataBaseModel):
    f_storage_engine = CharField(max_length=30)
    f_type = CharField(max_length=20)
    f_version = CharField(max_length=10, index=True)
    f_storage_path = CharField(max_length=256, null=True)
    f_snapshot_time = BigIntegerField(null=True)
    f_fate_flow_snapshot_time = BigIntegerField(null=True)
    f_dependencies_conf = JSONField(null=True)
    f_upload_status = BooleanField(default=False)
    f_pid = IntegerField(null=True)

    class Meta:
        db_table = "t_dependencies_storage_meta"
        primary_key = CompositeKey('f_storage_engine', 'f_type', 'f_version')
