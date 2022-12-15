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
from peewee import CharField, TextField, BigIntegerField, IntegerField, BooleanField, CompositeKey

from fate_flow.db.base_models import DataBaseModel, JSONField, DateTimeField


class Job(DataBaseModel):
    # multi-party common configuration
    f_job_id = CharField(max_length=25, index=True)
    f_name = CharField(max_length=500, null=True, default='')
    f_description = TextField(null=True, default='')
    f_tag = CharField(max_length=50, null=True, default='')
    f_dag = JSONField()
    f_parties = JSONField()

    f_initiator_party_id = CharField(max_length=50)
    f_scheduler_party_id = CharField(max_length=50)
    f_status = CharField(max_length=50)
    f_status_code = IntegerField(null=True)
    # this party configuration
    f_role = CharField(max_length=50, index=True)
    f_party_id = CharField(max_length=50, index=True)
    f_progress = IntegerField(null=True, default=0)
    f_model_id = CharField(max_length=100, null=True)
    f_model_version = IntegerField(null=True, default=0)

    f_engine_name = CharField(max_length=50, null=True)
    f_engine_type = CharField(max_length=10, null=True)
    f_cores = IntegerField(default=0)
    f_memory = IntegerField(default=0)  # MB
    f_remaining_cores = IntegerField(default=0)
    f_remaining_memory = IntegerField(default=0)  # MB
    f_resource_in_use = BooleanField(default=False)
    f_apply_resource_time = BigIntegerField(null=True)
    f_return_resource_time = BigIntegerField(null=True)

    f_start_time = BigIntegerField(null=True)
    f_start_date = DateTimeField(null=True)
    f_end_time = BigIntegerField(null=True)
    f_end_date = DateTimeField(null=True)
    f_elapsed = BigIntegerField(null=True)

    class Meta:
        db_table = "t_job"
        primary_key = CompositeKey('f_job_id', 'f_role', 'f_party_id')


class Task(DataBaseModel):
    f_job_id = CharField(max_length=25, index=True)
    f_role = CharField(max_length=50, index=True)
    f_party_id = CharField(max_length=50, index=True)
    f_task_name = CharField(max_length=50)
    f_component = CharField(max_length=50)
    f_task_id = CharField(max_length=100)
    f_task_version = BigIntegerField()
    f_execution_id = CharField(max_length=100)
    f_scheduler_party_id = CharField(max_length=50)
    f_federated_status_collect_type = CharField(max_length=10)
    f_status = CharField(max_length=50, index=True)
    f_status_code = IntegerField(null=True)
    f_auto_retries = IntegerField(default=0)
    f_auto_retry_delay = IntegerField(default=0)
    f_component_parameters = JSONField(null=True)

    f_worker_id = CharField(null=True, max_length=100)
    f_cmd = JSONField(null=True)
    f_run_ip = CharField(max_length=100, null=True)
    f_run_port = IntegerField(null=True)
    f_run_pid = IntegerField(null=True)
    f_party_status = CharField(max_length=50)
    f_provider_info = JSONField(null=True)
    f_task_parameters = JSONField(null=True)
    f_engine_conf = JSONField(null=True)
    f_kill_status = BooleanField(default=False)
    f_error_report = TextField(default="")

    f_start_time = BigIntegerField(null=True)
    f_start_date = DateTimeField(null=True)
    f_end_time = BigIntegerField(null=True)
    f_end_date = DateTimeField(null=True)
    f_elapsed = BigIntegerField(null=True)

    class Meta:
        db_table = "t_task"
        primary_key = CompositeKey('f_job_id', 'f_task_id', 'f_task_version', 'f_role', 'f_party_id')


class TrackingOutputInfo(DataBaseModel):
    f_job_id = CharField(max_length=25, index=True)
    f_task_id = CharField(max_length=100, null=True, index=True)
    f_task_version = BigIntegerField(null=True)
    f_task_name = CharField(max_length=50, index=True)
    f_role = CharField(max_length=50, index=True)
    f_party_id = CharField(max_length=10, index=True)
    f_output_key = CharField(max_length=30)
    f_type = CharField(max_length=10, null=True)
    f_uri = CharField(max_length=100, null=True)
    f_meta = JSONField()

    class Meta:
        db_table = "t_tracking_output"
        primary_key = CompositeKey('f_job_id', 'f_task_id', 'f_task_version', 'f_role', 'f_party_id', 'f_type', 'f_output_key')


class PipelineModelInfo(DataBaseModel):
    f_role = CharField(max_length=50)
    f_party_id = CharField(max_length=10)
    f_job_id = CharField(max_length=25, index=True)
    f_model_id = CharField(max_length=100, index=True)
    f_model_version = CharField(max_length=100, index=True)

    class Meta:
        db_table = "t_model_info"
        primary_key = CompositeKey('f_job_id')


class PipelineModelMeta(DataBaseModel):
    f_model_id = CharField(max_length=100, index=True)
    f_model_version = CharField(max_length=100, index=True)
    f_role = CharField(max_length=50, index=True)
    f_party_id = CharField(max_length=10, index=True)
    f_task_name = CharField(max_length=100, index=True)
    f_component = CharField(max_length=30, null=True)

    class Meta:
        db_table = 't_model_meta'
        primary_key = CompositeKey('f_role', 'f_party_id', 'f_model_id', 'f_model_version', 'f_task_name')


class EngineRegistry(DataBaseModel):
    f_engine_type = CharField(max_length=10, index=True)
    f_engine_name = CharField(max_length=50, index=True)
    f_engine_entrance = CharField(max_length=50, index=True)
    f_engine_config = JSONField()
    f_cores = IntegerField()
    f_memory = IntegerField()  # MB
    f_remaining_cores = IntegerField()
    f_remaining_memory = IntegerField()  # MB
    f_nodes = IntegerField()

    class Meta:
        db_table = "t_engine_registry"
        primary_key = CompositeKey('f_engine_name', 'f_engine_type')


class WorkerInfo(DataBaseModel):
    f_worker_id = CharField(max_length=100, primary_key=True)
    f_worker_name = CharField(max_length=50, index=True)
    f_job_id = CharField(max_length=25, index=True)
    f_task_id = CharField(max_length=100)
    f_task_version = BigIntegerField(index=True)
    f_role = CharField(max_length=50)
    f_party_id = CharField(max_length=50, index=True)
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
