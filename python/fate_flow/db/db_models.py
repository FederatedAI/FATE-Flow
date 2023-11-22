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

from peewee import CharField, TextField, BigIntegerField, IntegerField, BooleanField, CompositeKey, BigAutoField
from fate_flow.db.base_models import DataBaseModel, JSONField
from fate_flow.entity.types import PROTOCOL


class Job(DataBaseModel):
    f_protocol = CharField(max_length=50, default=PROTOCOL.FATE_FLOW)
    f_flow_id = CharField(max_length=25, default='')
    f_job_id = CharField(max_length=25, index=True)
    f_user_name = CharField(max_length=500, null=True, default='')
    f_description = TextField(null=True, default='')
    f_tag = CharField(max_length=50, null=True, default='')
    f_dag = JSONField()
    f_parties = JSONField()

    f_initiator_party_id = CharField(max_length=50)
    f_scheduler_party_id = CharField(max_length=50)
    f_status = CharField(max_length=50)
    f_status_code = IntegerField(null=True)

    f_inheritance = JSONField(null=True)

    # this party configuration
    f_role = CharField(max_length=50, index=True)
    f_party_id = CharField(max_length=50, index=True)
    f_progress = IntegerField(null=True, default=0)
    f_model_id = CharField(max_length=100, null=True)
    f_model_version = CharField(max_length=10)

    f_engine_name = CharField(max_length=50, null=True)
    f_cores = IntegerField(default=0)
    f_memory = IntegerField(default=0)  # MB
    f_remaining_cores = IntegerField(default=0)
    f_remaining_memory = IntegerField(default=0)  # MB
    f_resource_in_use = BooleanField(default=False)
    f_apply_resource_time = BigIntegerField(null=True)
    f_return_resource_time = BigIntegerField(null=True)

    f_start_time = BigIntegerField(null=True)
    f_end_time = BigIntegerField(null=True)
    f_elapsed = BigIntegerField(null=True)

    class Meta:
        db_table = "t_job"
        primary_key = CompositeKey('f_job_id', 'f_role', 'f_party_id')


class Task(DataBaseModel):
    f_protocol = CharField(max_length=50, default=PROTOCOL.FATE_FLOW)
    f_job_id = CharField(max_length=25, index=True)
    f_role = CharField(max_length=50, index=True)
    f_party_id = CharField(max_length=50, index=True)
    f_task_name = CharField(max_length=50)
    f_component = CharField(max_length=50)
    f_task_id = CharField(max_length=100)
    f_task_version = BigIntegerField()
    f_execution_id = CharField(max_length=100)
    f_scheduler_party_id = CharField(max_length=50)
    f_status = CharField(max_length=50, index=True)
    f_status_code = IntegerField(null=True)
    f_component_parameters = JSONField(null=True)
    f_task_run = JSONField(null=True)
    f_memory = IntegerField(default=0)
    f_task_cores = IntegerField(default=0)
    f_resource_in_use = BooleanField(default=False)

    f_worker_id = CharField(null=True, max_length=100)
    f_cmd = JSONField(null=True)
    f_run_ip = CharField(max_length=100, null=True)
    f_run_port = IntegerField(null=True)
    f_run_pid = IntegerField(null=True)
    f_party_status = CharField(max_length=50)
    f_provider_name = CharField(max_length=50)
    f_task_parameters = JSONField(null=True)
    f_engine_conf = JSONField(null=True)
    f_kill_status = BooleanField(default=False)
    f_error_report = TextField(default="")
    f_sync_type = CharField(max_length=20)
    f_timeout = IntegerField(null=True)

    f_launcher_name = CharField(max_length=20, null=True)
    f_launcher_conf = JSONField(null=True)

    f_start_time = BigIntegerField(null=True)
    f_end_time = BigIntegerField(null=True)
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
    f_party_id = CharField(max_length=50, index=True)
    f_output_key = CharField(max_length=30)
    f_index = IntegerField()
    f_uri = CharField(max_length=200, null=True)
    f_namespace = CharField(max_length=200)
    f_name = CharField(max_length=200)

    class Meta:
        db_table = "t_tracking_data_output"
        primary_key = CompositeKey('f_job_id', 'f_task_id', 'f_task_version', 'f_role', 'f_party_id', 'f_output_key', 'f_uri')


class EngineRegistry(DataBaseModel):
    f_engine_type = CharField(max_length=10, index=True)
    f_engine_name = CharField(max_length=50, index=True)
    f_engine_config = JSONField()
    f_cores = IntegerField()
    f_memory = IntegerField()  # MB
    f_remaining_cores = IntegerField()
    f_remaining_memory = IntegerField()  # MB

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
    f_end_time = BigIntegerField(null=True)

    class Meta:
        db_table = "t_worker"


class Metric(DataBaseModel):
    _mapper = {}

    @classmethod
    def model(cls, table_index=None, date=None):
        if not table_index:
            table_index = date.strftime(
                '%Y%m%d') if date else datetime.datetime.now().strftime(
                '%Y%m%d')
        class_name = 'Metric_%s' % table_index

        ModelClass = Metric._mapper.get(class_name, None)
        if ModelClass is None:
            class Meta:
                db_table = '%s_%s' % ('t_tracking_metric', table_index)

            attrs = {'__module__': cls.__module__, 'Meta': Meta}
            ModelClass = type("%s_%s" % (cls.__name__, table_index), (cls,),
                              attrs)
            Metric._mapper[class_name] = ModelClass
        return ModelClass()

    f_id = BigAutoField(primary_key=True)
    f_job_id = CharField(max_length=25, index=True)
    f_role = CharField(max_length=10, index=True)
    f_party_id = CharField(max_length=50)
    f_task_name = CharField(max_length=50, index=True)
    f_task_id = CharField(max_length=100)
    f_task_version = BigIntegerField(null=True)
    f_name = CharField(max_length=30, index=True)
    f_type = CharField(max_length=30, index=True, null=True)
    f_groups = JSONField()
    f_step_axis = CharField(max_length=30, index=True, null=True)
    f_data = JSONField()


class ProviderInfo(DataBaseModel):
    f_provider_name = CharField(max_length=100, primary_key=True)
    f_name = CharField(max_length=20, index=True)
    f_version = CharField(max_length=20)
    f_device = CharField(max_length=20)
    f_metadata = JSONField()

    class Meta:
        db_table = "t_provider_info"


class ComponentInfo(DataBaseModel):
    f_provider_name = CharField(max_length=100)
    f_protocol = CharField(max_length=20, default=PROTOCOL.FATE_FLOW)
    f_name = CharField(max_length=20, index=True)
    f_version = CharField(max_length=20)
    f_device = CharField(max_length=20)
    f_component_name = CharField(max_length=50)
    f_component_entrypoint = JSONField(null=True)
    f_component_description = JSONField(null=True)

    class Meta:
        db_table = "t_component_info"
        primary_key = CompositeKey("f_provider_name", "f_component_name", "f_protocol")


class PipelineModelMeta(DataBaseModel):
    f_model_id = CharField(max_length=100)
    f_model_version = CharField(max_length=10)
    f_job_id = CharField(max_length=25, index=True)
    f_role = CharField(max_length=50, index=True)
    f_party_id = CharField(max_length=50, index=True)
    f_task_name = CharField(max_length=50, index=True)
    f_storage_key = CharField(max_length=100)
    f_output_key = CharField(max_length=20)
    f_type_name = CharField(max_length=20)
    f_meta_data = JSONField(null=True)
    f_storage_engine = CharField(max_length=30, null=True, index=True)

    class Meta:
        db_table = 't_model_meta'
        primary_key = CompositeKey('f_job_id', 'f_storage_key', "f_storage_engine")


class ServerRegistryInfo(DataBaseModel):
    f_server_name = CharField(max_length=30, index=True)
    f_host = CharField(max_length=30)
    f_port = IntegerField()
    f_protocol = CharField(max_length=10)

    class Meta:
        db_table = "t_server"


class ServiceRegistryInfo(DataBaseModel):
    f_server_name = CharField(max_length=30)
    f_service_name = CharField(max_length=30)
    f_url = CharField(max_length=100)
    f_method = CharField(max_length=10)
    f_params = JSONField(null=True)
    f_data = JSONField(null=True)
    f_headers = JSONField(null=True)

    class Meta:
        db_table = "t_service"
        primary_key = CompositeKey('f_server_name', 'f_service_name')
