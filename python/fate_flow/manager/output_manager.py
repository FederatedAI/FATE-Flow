import operator

from fate_flow.db.base_models import DB, BaseModelOperate
from fate_flow.db.db_models import TrackingOutputInfo, Metric
from fate_flow.entity.output_types import MetricData
from fate_flow.utils import db_utils
from fate_flow.utils.log_utils import schedule_logger


class OutputDataTracking(BaseModelOperate):
    @classmethod
    def create(cls, entity_info):
        # name, namespace, key, meta, job_id, role, party_id, task_id, task_version
        cls._create_entity(TrackingOutputInfo, entity_info)

    @classmethod
    def query(cls, reverse=False, **kwargs):
        return cls._query(TrackingOutputInfo, reverse=reverse, **kwargs)


class OutputModel(BaseModelOperate):
    @classmethod
    def create(cls, entity_info):
        # name, namespace, key, meta, job_id, role, party_id, task_id, task_version
        cls._create_entity(TrackingOutputInfo, entity_info)

    @classmethod
    def query(cls, reverse=False, **kwargs):
        return cls._query(TrackingOutputInfo, reverse=reverse, **kwargs)


class OutputMetric:
    def __init__(self, job_id: str, role: str, party_id: str, task_name: str, task_id: str = None,
                 task_version: int = None):
        self.job_id = job_id
        self.role = role
        self.party_id = party_id
        self.task_name = task_name
        self.task_id = task_id
        self.task_version = task_version

    def save_output_metrics(self, data, incomplete):
        return self._insert_metrics_into_db(MetricData(**data), incomplete)

    @DB.connection_context()
    def _insert_metrics_into_db(self, data: MetricData, incomplete: bool):
        try:
            model_class = self.get_model_class()
            if not model_class.table_exists():
                model_class.create_table()
            tracking_metric = model_class()
            tracking_metric.f_job_id = self.job_id
            tracking_metric.f_task_id = self.task_id
            tracking_metric.f_task_version = self.task_version
            tracking_metric.f_role = self.role
            tracking_metric.f_party_id = self.party_id
            tracking_metric.f_task_name = self.task_name

            tracking_metric.f_namespace = data.namespace
            tracking_metric.f_name = data.name
            tracking_metric.f_type = data.type
            tracking_metric.f_groups = data.groups
            tracking_metric.f_metadata = data.metadata
            tracking_metric.f_data = data.data
            tracking_metric.f_incomplete = incomplete
            tracking_metric.save()
        except Exception as e:
            schedule_logger(self.job_id).exception(
                "An exception where inserted metric {} of metric namespace: {} to database:\n{}".format(
                    data.name,
                    data.namespace,
                    e
                ))

    @DB.connection_context()
    def read_metrics(self, filters_args: dict = None):
        try:
            if not filters_args:
                filters_args = {}
            tracking_metric_model = self.get_model_class()
            key_list = ["namespace", "name", "type", "groups", "incomplete"]
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
                tracking_metric_model.f_data, tracking_metric_model.f_metadata
            ).where(*filters)
            return [metric.to_human_model_dict() for metric in metrics]
        except Exception as e:
            schedule_logger(self.job_id).exception(e)
            raise e

    @DB.connection_context()
    def query_metric_keys(self):
        try:
            tracking_metric_model = self.get_model_class()
            metrics = tracking_metric_model.select(
                tracking_metric_model.f_namespace,
                tracking_metric_model.f_name,
                tracking_metric_model.f_type,
                tracking_metric_model.f_groups,
                tracking_metric_model.f_incomplete
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
    def clean_metrics(self):
        tracking_metric_model = self.get_model_class()
        operate = tracking_metric_model.delete().where(
            tracking_metric_model.f_task_id == self.task_id,
            tracking_metric_model.f_task_version == self.task_version,
            tracking_metric_model.f_role == self.role,
            tracking_metric_model.f_party_id == self.party_id
        )
        return operate.execute() > 0

    def get_model_class(self):
        return db_utils.get_dynamic_db_model(Metric, self.job_id)
