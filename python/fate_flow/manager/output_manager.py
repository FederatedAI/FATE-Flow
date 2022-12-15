from fate_flow.db.base_models import DB, BaseModelOperate
from fate_flow.db.db_models import TrackingOutputInfo


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

