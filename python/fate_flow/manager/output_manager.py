import peewee

from fate_flow.db.base_models import DB
from fate_flow.db.db_models import TrackingOutputDataInfo
from fate_flow.utils.base_utils import current_timestamp
from fate_flow.utils.log_utils import sql_logger


class Tracking:
    @classmethod
    @DB.connection_context()
    def create_entity(cls, entity_model: object, entity_info: object) -> object:
        obj = entity_model()
        obj.f_create_time = current_timestamp()
        for k, v in entity_info.items():
            attr_name = 'f_%s' % k
            if hasattr(entity_model, attr_name):
                setattr(obj, attr_name, v)
        try:
            rows = obj.save(force_insert=True)
            if rows != 1:
                raise Exception("Create {} failed".format(entity_model))
            return obj
        except peewee.IntegrityError as e:
            if e.args[0] == 1062 or (isinstance(e.args[0], str) and "UNIQUE constraint failed" in e.args[0]):
                sql_logger(job_id=entity_info.get("job_id", "fate_flow")).warning(e)
            else:
                raise Exception("Create {} failed:\n{}".format(entity_model, e))
        except Exception as e:
            raise Exception("Create {} failed:\n{}".format(entity_model, e))


class OutputDataTracking(Tracking):
    @classmethod
    @DB.connection_context()
    def create(cls, entity_info):
        # name, namespace, key, meta, job_id, role, party_id, task_id, task_version
        cls.create_entity(TrackingOutputDataInfo, entity_info)

    @classmethod
    @DB.connection_context()
    def query(cls, reverse=False, **kwargs):
        return TrackingOutputDataInfo.query(reverse=reverse, **kwargs)

