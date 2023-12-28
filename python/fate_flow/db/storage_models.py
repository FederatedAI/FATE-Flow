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
from peewee import CharField, IntegerField, BooleanField, BigIntegerField, TextField, DateTimeField, CompositeKey

from fate_flow.db.base_models import DataBaseModel, JSONField


class StorageConnectorModel(DataBaseModel):
    f_name = CharField(max_length=100, primary_key=True)
    f_engine = CharField(max_length=100, index=True)  # 'MYSQL'
    f_connector_info = JSONField()

    class Meta:
        db_table = "t_storage_connector"


class StorageTableMetaModel(DataBaseModel):
    f_name = CharField(max_length=100, index=True)
    f_namespace = CharField(max_length=100, index=True)
    f_address = JSONField()
    f_engine = CharField(max_length=100)  # 'EGGROLL', 'MYSQL'
    f_options = JSONField()
    f_partitions = IntegerField(null=True)

    f_delimiter = CharField(null=True)
    f_have_head = BooleanField(default=True)
    f_extend_sid = BooleanField(default=False)
    f_data_meta = JSONField()
    f_count = BigIntegerField(null=True)
    f_part_of_data = JSONField()
    f_source = JSONField()
    f_data_type = CharField(max_length=20, null=True)
    f_disable = BooleanField(default=False)
    f_description = TextField(default='')

    f_read_access_time = BigIntegerField(null=True)
    f_write_access_time = BigIntegerField(null=True)

    class Meta:
        db_table = "t_storage_table_meta"
        primary_key = CompositeKey('f_name', 'f_namespace')


class SessionRecord(DataBaseModel):
    f_engine_session_id = CharField(max_length=150, null=False)
    f_manager_session_id = CharField(max_length=150, null=False)
    f_engine_type = CharField(max_length=10, index=True)
    f_engine_name = CharField(max_length=50, index=True)
    f_engine_address = JSONField()

    class Meta:
        db_table = "t_session_record"
        primary_key = CompositeKey("f_engine_type", "f_engine_name", "f_engine_session_id")
