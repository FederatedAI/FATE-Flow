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

from fate_arch.common.base_utils import current_timestamp, serialize_b64, deserialize_b64
from fate_flow.utils.log_utils import schedule_logger
from fate_flow.db import db_utils
from fate_flow.db.db_models import (DB, TrackingMetric)
from fate_flow.entity import Metric
from fate_flow.utils import job_utils


class MetricManager:
    def __init__(self, job_id: str, role: str, party_id: int,
                 component_name: str,
                 task_id: str = None,
                 task_version: int = None):
        self.job_id = job_id
        self.role = role
        self.party_id = party_id
        self.component_name = component_name
        self.task_id = task_id
        self.task_version = task_version

    @DB.connection_context()
    def read_metric_data(self, metric_namespace: str, metric_name: str, job_level=False):
        metrics = []
        for k, v in self.read_metrics_from_db(metric_namespace, metric_name, 1, job_level):
            metrics.append(Metric(key=k, value=v))
        return metrics

    @DB.connection_context()
    def insert_metrics_into_db(self, metric_namespace: str, metric_name: str, data_type: int, kv, job_level=False):
        try:
            model_class = self.get_model_class()
            tracking_metric = model_class()
            tracking_metric.f_job_id = self.job_id
            tracking_metric.f_component_name = (
                self.component_name if not job_level else job_utils.job_pipeline_component_name())
            tracking_metric.f_task_id = self.task_id
            tracking_metric.f_task_version = self.task_version
            tracking_metric.f_role = self.role
            tracking_metric.f_party_id = self.party_id
            tracking_metric.f_metric_namespace = metric_namespace
            tracking_metric.f_metric_name = metric_name
            tracking_metric.f_type = data_type
            default_db_source = tracking_metric.to_dict()
            tracking_metric_data_source = []
            for k, v in kv:
                db_source = default_db_source.copy()
                db_source['f_key'] = serialize_b64(k)
                db_source['f_value'] = serialize_b64(v)
                db_source['f_create_time'] = current_timestamp()
                tracking_metric_data_source.append(db_source)
            db_utils.bulk_insert_into_db(model_class, tracking_metric_data_source, schedule_logger(self.job_id))
        except Exception as e:
            schedule_logger(self.job_id).exception(
                "An exception where inserted metric {} of metric namespace: {} to database:\n{}".format(
                    metric_name,
                    metric_namespace,
                    e
                ))

    @DB.connection_context()
    def read_metrics_from_db(self, metric_namespace: str, metric_name: str, data_type, job_level=False):
        metrics = []
        try:
            tracking_metric_model = self.get_model_class()
            tracking_metrics = tracking_metric_model.select(tracking_metric_model.f_key,
                                                            tracking_metric_model.f_value).where(
                tracking_metric_model.f_job_id == self.job_id,
                tracking_metric_model.f_component_name == (
                    self.component_name if not job_level else job_utils.job_pipeline_component_name()),
                tracking_metric_model.f_role == self.role,
                tracking_metric_model.f_party_id == self.party_id,
                tracking_metric_model.f_metric_namespace == metric_namespace,
                tracking_metric_model.f_metric_name == metric_name,
                tracking_metric_model.f_type == data_type
            )
            for tracking_metric in tracking_metrics:
                yield deserialize_b64(tracking_metric.f_key), deserialize_b64(tracking_metric.f_value)
        except Exception as e:
            schedule_logger(self.job_id).exception(e)
            raise e
        return metrics

    @DB.connection_context()
    def clean_metrics(self):
        tracking_metric_model = self.get_model_class()
        operate = tracking_metric_model.delete().where(
            tracking_metric_model.f_task_id == self.task_id,
            tracking_metric_model.f_task_version == self.task_version,
            tracking_metric_model.f_role == self.role,
            tracking_metric_model.f_party_id == self.party_id
        )
        return operate.execute() > 0

    @DB.connection_context()
    def get_metric_list(self, job_level: bool = False):
        metrics = {}

        tracking_metric_model = self.get_model_class()
        if tracking_metric_model.table_exists():
            tracking_metrics = tracking_metric_model.select(
                tracking_metric_model.f_metric_namespace,
                tracking_metric_model.f_metric_name
            ).where(
                tracking_metric_model.f_job_id == self.job_id,
                tracking_metric_model.f_component_name == (self.component_name if not job_level else 'dag'),
                tracking_metric_model.f_role == self.role,
                tracking_metric_model.f_party_id == self.party_id
            ).distinct()

            for tracking_metric in tracking_metrics:
                metrics[tracking_metric.f_metric_namespace] = metrics.get(tracking_metric.f_metric_namespace, [])
                metrics[tracking_metric.f_metric_namespace].append(tracking_metric.f_metric_name)

        return metrics

    @DB.connection_context()
    def read_component_metrics(self):
        try:
            tracking_metric_model = self.get_model_class()
            tracking_metrics = tracking_metric_model.select().where(
                tracking_metric_model.f_job_id == self.job_id,
                tracking_metric_model.f_component_name == self.component_name,
                tracking_metric_model.f_role == self.role,
                tracking_metric_model.f_party_id == self.party_id,
                tracking_metric_model.f_task_version == self.task_version
            )
            return [tracking_metric for tracking_metric in tracking_metrics]
        except Exception as e:
            schedule_logger(self.job_id).exception(e)
            raise e

    @DB.connection_context()
    def reload_metric(self, source_metric_manager):
        component_metrics = source_metric_manager.read_component_metrics()
        for component_metric in component_metrics:
            model_class = self.get_model_class()
            tracking_metric = model_class()
            tracking_metric.f_job_id = self.job_id
            tracking_metric.f_component_name = self.component_name
            tracking_metric.f_task_id = self.task_id
            tracking_metric.f_task_version = self.task_version
            tracking_metric.f_role = self.role
            tracking_metric.f_party_id = self.party_id
            tracking_metric.f_metric_namespace = component_metric.f_metric_namespace
            tracking_metric.f_metric_name = component_metric.f_metric_name
            tracking_metric.f_type = component_metric.f_type
            tracking_metric.f_key = component_metric.f_key
            tracking_metric.f_value = component_metric.f_value
            tracking_metric.save()

    def get_model_class(self):
        return db_utils.get_dynamic_db_model(TrackingMetric, self.job_id)
