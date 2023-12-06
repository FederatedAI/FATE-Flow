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
from peewee import CharField, TextField, IntegerField, BooleanField, BigIntegerField, CompositeKey

from fate_flow.db.base_models import DataBaseModel, JSONField
from fate_flow.entity.types import PROTOCOL


class ScheduleJob(DataBaseModel):
    f_protocol = CharField(max_length=50, default=PROTOCOL.FATE_FLOW)
    f_job_id = CharField(max_length=25, index=True)
    f_priority = IntegerField(default=0)
    f_tag = CharField(max_length=50, null=True, default='')
    f_dag = JSONField(null=True)
    f_parties = JSONField()
    f_initiator_party_id = CharField(max_length=50)
    f_scheduler_party_id = CharField(max_length=50)
    f_status = CharField(max_length=50)
    f_status_code = IntegerField(null=True)

    f_progress = IntegerField(null=True, default=0)
    f_schedule_signal = BooleanField(default=False)
    f_schedule_time = BigIntegerField(null=True)
    f_cancel_signal = BooleanField(default=False)
    f_cancel_time = BigIntegerField(null=True)
    f_rerun_signal = BooleanField(default=False)
    f_end_scheduling_updates = IntegerField(null=True, default=0)

    f_start_time = BigIntegerField(null=True)
    f_end_time = BigIntegerField(null=True)
    f_elapsed = BigIntegerField(null=True)

    class Meta:
        db_table = "t_schedule_job"
        primary_key = CompositeKey('f_job_id')


class ScheduleTask(DataBaseModel):
    f_job_id = CharField(max_length=25, index=True)
    f_role = CharField(max_length=50, index=True)
    f_party_id = CharField(max_length=50, index=True)
    f_task_name = CharField(max_length=50)
    f_component = CharField(max_length=50)
    f_task_id = CharField(max_length=100)
    f_task_version = BigIntegerField()
    f_parties = JSONField()
    f_error_report = TextField(default="")
    f_status = CharField(max_length=50)

    f_start_time = BigIntegerField(null=True)
    f_end_time = BigIntegerField(null=True)
    f_elapsed = BigIntegerField(null=True)

    class Meta:
        db_table = "t_schedule_task"
        primary_key = CompositeKey('f_job_id', 'f_task_id', 'f_task_version', 'f_role', 'f_party_id')


class ScheduleTaskStatus(DataBaseModel):
    f_job_id = CharField(max_length=25, index=True)
    f_task_name = CharField(max_length=50)
    f_task_id = CharField(max_length=100)
    f_task_version = BigIntegerField()
    f_status = CharField(max_length=50)
    f_auto_retries = IntegerField(default=0)
    f_sync_type = CharField(max_length=10)

    class Meta:
        db_table = "t_schedule_task_status"
        primary_key = CompositeKey('f_job_id', 'f_task_id', 'f_task_version')

