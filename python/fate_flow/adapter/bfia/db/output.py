from peewee import CompositeKey, CharField, TextField, BigIntegerField

from fate_flow.db import DataBaseModel, JSONField


class ComponentOutput(DataBaseModel):
    f_job_id = CharField(max_length=25, index=True)
    f_role = CharField(max_length=50, index=True)
    f_node_id = CharField(max_length=50, index=True)
    f_task_name = CharField(max_length=50)
    f_component = CharField(max_length=50)
    f_task_id = CharField(max_length=100)
    f_type = CharField(max_length=20)
    f_key = CharField(max_length=20)
    f_engine = JSONField()
    f_address = JSONField()

    class Meta:
        db_table = "t_bfia_component_output"
        primary_key = CompositeKey('f_job_id', 'f_role', 'f_node_id', 'f_task_id', 'f_type', 'f_key')
