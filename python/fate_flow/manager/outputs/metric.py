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
import operator
from typing import List

from fate_flow.db.base_models import DB
from fate_flow.db.db_models import Metric
from fate_flow.entity.spec.dag import MetricData
from fate_flow.utils import db_utils
from fate_flow.utils.log_utils import schedule_logger


class OutputMetric:
    def __init__(self, job_id: str, role: str, party_id: str, task_name: str, task_id: str = None,
                 task_version: int = None):
        self.job_id = job_id
        self.role = role
        self.party_id = party_id
        self.task_name = task_name
        self.task_id = task_id
        self.task_version = task_version

    def save_output_metrics(self, data):
        if not data or not isinstance(data, list):
            raise RuntimeError(f"Save metric data failed, data is {data}")
        return self._insert_metrics_into_db(
            self.job_id, self.role, self.party_id, self.task_id, self.task_version,  self.task_name, data
        )

    def save_as(self, job_id, role, party_id, task_name, task_id, task_version):
        data_list = self.read_metrics()
        self._insert_metrics_into_db(
            job_id, role, party_id, task_id, task_version, task_name, data_list
        )

    @DB.connection_context()
    def _insert_metrics_into_db(self, job_id, role, party_id, task_id, task_version, task_name, data_list):
        model_class = self.get_model_class(job_id)
        if not model_class.table_exists():
            model_class.create_table()
        metric_list = [{
            "f_job_id": job_id,
            "f_task_id": task_id,
            "f_task_version": task_version,
            "f_role": role,
            "f_party_id": party_id,
            "f_task_name": task_name,
            "f_name": data.get("name"),
            "f_type": data.get("type"),
            "f_groups": data.get("groups"),
            "f_step_axis": data.get("step_axis"),
            "f_data": data.get("data")

        } for data in data_list]

        with DB.atomic():
            for i in range(0, len(metric_list), 100):
                model_class.insert_many(metric_list[i: i+100]).execute()

    @DB.connection_context()
    def read_metrics(self, filters_args: dict = None):
        try:
            if not filters_args:
                filters_args = {}
            tracking_metric_model = self.get_model_class(self.job_id)
            key_list = ["name", "type", "groups", "step_axis"]
            filters = [
                tracking_metric_model.f_job_id == self.job_id,
                tracking_metric_model.f_role == self.role,
                tracking_metric_model.f_party_id == self.party_id,
                tracking_metric_model.f_task_id == self.task_id,
                tracking_metric_model.f_task_version == self.task_version
            ]
            for k, v in filters_args.items():
                if k in key_list:
                    if v is not None:
                        filters.append(operator.attrgetter(f"f_{k}")(tracking_metric_model) == v)
            metrics = tracking_metric_model.select(
                tracking_metric_model.f_name,
                tracking_metric_model.f_type,
                tracking_metric_model.f_groups,
                tracking_metric_model.f_step_axis,
                tracking_metric_model.f_data
            ).where(*filters)
            return [metric.to_human_model_dict() for metric in metrics]
        except Exception as e:
            schedule_logger(self.job_id).exception(e)
            raise e

    @DB.connection_context()
    def query_metric_keys(self):
        try:
            tracking_metric_model = self.get_model_class(self.job_id)
            metrics = tracking_metric_model.select(
                tracking_metric_model.f_name,
                tracking_metric_model.f_type,
                tracking_metric_model.f_groups,
                tracking_metric_model.f_step_axis
            ).where(
                tracking_metric_model.f_job_id == self.job_id,
                tracking_metric_model.f_role == self.role,
                tracking_metric_model.f_party_id == self.party_id,
                tracking_metric_model.f_task_id == self.task_id,
                tracking_metric_model.f_task_version == self.task_version
            ).distinct()
            return [metric.to_human_model_dict() for metric in metrics]
        except Exception as e:
            schedule_logger(self.job_id).exception(e)
            raise e

    @DB.connection_context()
    def delete_metrics(self):
        tracking_metric_model = self.get_model_class(self.job_id)
        operate = tracking_metric_model.delete().where(
            tracking_metric_model.f_task_id == self.task_id,
            tracking_metric_model.f_role == self.role,
            tracking_metric_model.f_party_id == self.party_id
        )
        return operate.execute() > 0

    @staticmethod
    def get_model_class(job_id):
        return db_utils.get_dynamic_db_model(Metric, job_id)
