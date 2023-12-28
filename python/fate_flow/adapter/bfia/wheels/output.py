from fate_flow.adapter.bfia.db import ComponentOutput
from fate_flow.db.base_models import BaseModelOperate
from fate_flow.utils.wraps_utils import filter_parameters


class OutputMeta(BaseModelOperate):
    @classmethod
    def save(cls, **meta_info):
        cls._create_entity(ComponentOutput, meta_info)

    @classmethod
    @filter_parameters()
    def query(cls, **kwargs):
        return cls._query(ComponentOutput, **kwargs)

    @classmethod
    @filter_parameters()
    def delete(cls, **kwargs):
        return cls._delete(ComponentOutput, **kwargs)
