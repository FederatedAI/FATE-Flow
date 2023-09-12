from peewee import CompositeKey, CharField, TextField

from fate_flow.db import DataBaseModel, JSONField


class AdapterJob(DataBaseModel):
    f_job_id = CharField(max_length=25, index=True)
    f_user_name = CharField(max_length=500, null=True, default='')
    f_description = TextField(null=True, default='')
    f_tag = CharField(max_length=50, null=True, default='')
    f_dag = JSONField()
    f_parties = JSONField()

    class Meta:
        db_table = "t_adapter_job"
        primary_key = CompositeKey('f_job_id')
