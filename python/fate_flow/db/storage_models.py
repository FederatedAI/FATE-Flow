from peewee import CharField, IntegerField, BooleanField, BigIntegerField, TextField, DateTimeField, CompositeKey

from fate_flow.db.base_models import DataBaseModel, JSONField, SerializedField


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
    f_store_type = CharField(max_length=50, null=True)  # store type
    f_options = JSONField()
    f_partitions = IntegerField(null=True)

    f_id_delimiter = CharField(null=True)
    f_in_serialized = BooleanField(default=True)
    f_have_head = BooleanField(default=True)
    f_extend_sid = BooleanField(default=False)
    f_auto_increasing_sid = BooleanField(default=False)

    f_schema = SerializedField()
    f_count = BigIntegerField(null=True)
    f_part_of_data = SerializedField()
    f_origin = CharField(max_length=50, default='')
    f_disable = BooleanField(default=False)
    f_description = TextField(default='')

    f_read_access_time = BigIntegerField(null=True)
    f_read_access_date = DateTimeField(null=True)
    f_write_access_time = BigIntegerField(null=True)
    f_write_access_date = DateTimeField(null=True)

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
