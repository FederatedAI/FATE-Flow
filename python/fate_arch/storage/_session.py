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
import os.path

from fate_arch.abc import StorageSessionABC, StorageTableABC, CTableABC
from fate_arch.common import EngineType
from fate_arch.common.base_utils import current_timestamp
from fate_arch.common.log import getLogger
from fate_arch.storage._table import StorageTableMeta
from fate_arch.storage._types import StorageEngine, Relationship
from fate_arch.storage.metastore.db_models import DB, StorageTableMetaModel, SessionRecord

MAX_NUM = 10000

LOGGER = getLogger()


class StorageSessionBase(StorageSessionABC):
    def __init__(self, session_id, engine_name):
        self._session_id = session_id
        self._engine_name = engine_name
        self._default_name = None
        self._default_namespace = None

    def create(self):
        raise NotImplementedError()

    def create_table(self, address, name, namespace, partitions=None, **kwargs):
        table = self.table(address=address, name=name, namespace=namespace, partitions=partitions, **kwargs)
        table_meta = StorageTableMeta(name=name, namespace=namespace, new=True)
        table_meta.set_metas(**kwargs)
        table_meta.address = table.get_address()
        table_meta.partitions = table.get_partitions()
        table_meta.engine = table.get_engine()
        table_meta.type = table.get_store_type()
        table_meta.options = table.get_options()
        table_meta.create()
        table.set_meta(table_meta)
        # update count on meta
        # table.count()
        return table

    def set_default(self, name, namespace):
        self._default_name = name
        self._default_namespace = namespace

    def get_table(self, name=None, namespace=None):
        if not name or not namespace:
            name = self._default_name
            namespace = self._default_namespace
        meta = StorageTableMeta(name=name, namespace=namespace)
        if meta:
            table = self.table(name=meta.get_name(),
                               namespace=meta.get_namespace(),
                               address=meta.get_address(),
                               partitions=meta.get_partitions(),
                               storage_type=meta.get_type(),
                               options=meta.get_options())
            table.set_meta(meta)
            return table
        else:
            return None

    def table(self, name, namespace, address, partitions, storage_type=None, options=None, **kwargs) -> StorageTableABC:
        raise NotImplementedError()

    @classmethod
    def copy_from_computing(cls, computing_table: CTableABC, table_namespace, table_name, engine=None, engine_address=None, store_type=None):
        partitions = computing_table.partitions
        address_dict = engine_address.copy()
        if engine:
            if engine not in Relationship.CompToStore.get(computing_table.engine, {}).get("support", []):
                raise Exception(f"storage engine {engine} not supported with computing engine {computing_table.engine}")
        else:
            engine = Relationship.CompToStore.get(computing_table.engine, {}).get("default", None)
            if not engine:
                raise Exception(f"can not found {computing_table.engine} default storage engine")
        if engine == StorageEngine.EGGROLL:
            address_dict.update({"name": table_name, "namespace": table_namespace})
        elif engine == StorageEngine.STANDALONE:
            address_dict.update({"name": table_name, "namespace": table_namespace})
        elif engine == StorageEngine.HDFS:
            address_dict.update({"path": os.path.join(address_dict.get("path_prefix", ""), table_namespace, table_name)})
        else:
            raise RuntimeError(f"{engine} storage is not supported")
        address = StorageTableMeta.create_address(storage_engine=engine, address_dict=address_dict)
        schema = {}
        # persistent table
        computing_table.save(address, schema=schema, partitions=partitions)
        part_of_data = []
        part_of_limit = 100
        for k, v in computing_table.collect():
            part_of_data.append((k, v))
            part_of_limit -= 1
            if part_of_limit == 0:
                break
        table_count = computing_table.count()
        table_meta = StorageTableMeta(name=table_name, namespace=table_namespace, new=True)
        table_meta.address = address
        table_meta.partitions = computing_table.partitions
        table_meta.engine = engine
        table_meta.type = store_type
        table_meta.schema = schema
        table_meta.part_of_data = part_of_data
        table_meta.count = table_count
        table_meta.create()
        return table_meta

    @classmethod
    @DB.connection_context()
    def get_storage_info(cls, name, namespace):
        metas = StorageTableMetaModel.select().where(StorageTableMetaModel.f_name == name,
                                                     StorageTableMetaModel.f_namespace == namespace)
        if metas:
            meta = metas[0]
            engine = meta.f_engine
            address_dict = meta.f_address
            address = StorageTableMeta.create_address(storage_engine=engine, address_dict=address_dict)
            partitions = meta.f_partitions
            return engine, address, partitions
        else:
            return None, None, None

    def __enter__(self):
        with DB.connection_context():
            session_record = SessionRecord()
            session_record.f_session_id = self._session_id
            session_record.f_engine_name = self._engine_name
            session_record.f_engine_type = EngineType.STORAGE
            # TODO: engine address
            session_record.f_engine_address = {}
            session_record.f_create_time = current_timestamp()
            rows = session_record.save(force_insert=True)
            if rows != 1:
                raise Exception(f"create session record {self._session_id} failed")
            LOGGER.debug(f"save session {self._session_id} record")
        self.create()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.destroy()

    def destroy(self):
        try:
            self.close()
        except Exception as e:
            LOGGER.warning(e)
        with DB.connection_context():
            rows = SessionRecord.delete().where(SessionRecord.f_session_id == self._session_id).execute()
            if rows > 0:
                LOGGER.debug(f"delete session {self._session_id} record")
            else:
                LOGGER.warning(f"failed delete session {self._session_id} record")

    @classmethod
    @DB.connection_context()
    def query_expired_sessions_record(cls, ttl) -> [SessionRecord]:
        sessions_record = SessionRecord.select().where(SessionRecord.f_create_time < (current_timestamp() - ttl))
        return [session_record for session_record in sessions_record]

    def close(self):
        try:
            self.stop()
        except Exception as e:
            self.kill()

    def stop(self):
        raise NotImplementedError()

    def kill(self):
        raise NotImplementedError()

    def session_id(self):
        return self._session_id
