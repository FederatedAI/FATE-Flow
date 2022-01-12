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
import typing

from fate_arch import session, storage
from fate_arch.abc import CTableABC
from fate_arch.common import DTable
from fate_arch.common.base_utils import current_timestamp
from fate_flow.db.db_models import DB, CacheRecord
from fate_flow.entity import DataCache
from fate_flow.utils import base_utils


class CacheManager:
    @classmethod
    def persistent(cls, cache_name: str, cache_data: typing.Dict[str, CTableABC], cache_meta: dict, output_namespace: str,
                   output_name: str, output_storage_engine: str, output_storage_address: dict,
                   token=None) -> DataCache:
        cache = DataCache(name=cache_name, meta=cache_meta)
        for name, table in cache_data.items():
            table_meta = session.Session.persistent(computing_table=table,
                                                    namespace=output_namespace,
                                                    name=f"{output_name}_{name}",
                                                    schema=None,
                                                    engine=output_storage_engine,
                                                    engine_address=output_storage_address,
                                                    token=token)
            cache.data[name] = DTable(namespace=table_meta.namespace, name=table_meta.name,
                                      partitions=table_meta.partitions)
        return cache

    @classmethod
    def load(cls, cache: DataCache) -> typing.Tuple[typing.Dict[str, CTableABC], dict]:
        cache_data = {}
        for name, table in cache.data.items():
            storage_table_meta = storage.StorageTableMeta(name=table.name, namespace=table.namespace)
            computing_table = session.get_computing_session().load(
                storage_table_meta.get_address(),
                schema=storage_table_meta.get_schema(),
                partitions=table.partitions)
            cache_data[name] = computing_table
        return cache_data, cache.meta

    @classmethod
    @DB.connection_context()
    def record(cls, cache: DataCache, job_id: str = None, role: str = None, party_id: int = None, component_name: str = None, task_id: str = None, task_version: int = None,
               cache_name: str = None):
        for attr in {"job_id", "component_name", "task_id", "task_version"}:
            if getattr(cache, attr) is None and locals().get(attr) is not None:
                setattr(cache, attr, locals().get(attr))
        record = CacheRecord()
        record.f_create_time = current_timestamp()
        record.f_cache_key = base_utils.new_unique_id()
        cache.key = record.f_cache_key
        record.f_cache = cache
        record.f_job_id = job_id
        record.f_role = role
        record.f_party_id = party_id
        record.f_component_name = component_name
        record.f_task_id = task_id
        record.f_task_version = task_version
        record.f_cache_name = cache_name
        rows = record.save(force_insert=True)
        if rows != 1:
            raise Exception("save cache tracking failed")
        return record.f_cache_key

    @classmethod
    @DB.connection_context()
    def query(cls, cache_key: str = None, role: str = None, party_id: int = None, component_name: str = None, cache_name: str = None,
              **kwargs) -> typing.List[DataCache]:
        if cache_key is not None:
            records = CacheRecord.query(cache_key=cache_key)
        else:
            records = CacheRecord.query(role=role, party_id=party_id, component_name=component_name,
                                        cache_name=cache_name, **kwargs)
        return [record.f_cache for record in records]

    @classmethod
    @DB.connection_context()
    def query_record(cls, role: str = None, party_id: int = None, component_name: str = None, **kwargs) -> typing.List[CacheRecord]:
        records = CacheRecord.query(role=role, party_id=party_id, component_name=component_name, **kwargs)
        return [record for record in records]