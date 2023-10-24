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
import uuid

import peewee

from fate_flow.db.base_models import DB
from fate_flow.db.storage_models import SessionRecord
from fate_flow.engine.storage._abc import (
    StorageSessionABC,
    StorageTableABC,
    StorageTableMetaABC,
)

from fate_flow.engine.storage._table import StorageTableMeta
from fate_flow.entity.types import EngineType, StorageEngine
from fate_flow.runtime.system_settings import ENGINES
from fate_flow.utils import base_utils
from fate_flow.utils.log import getLogger

LOGGER = getLogger("storage")


class StorageSessionBase(StorageSessionABC):
    def __init__(self, session_id, engine):
        self._session_id = session_id
        self._engine = engine

    def create_table(
        self,
        address,
        name,
        namespace,
        partitions,
        key_serdes_type=0,
        value_serdes_type=0,
        partitioner_type=0,
        **kwargs,
    ):
        table = self.table(
            address=address,
            name=name,
            namespace=namespace,
            partitions=partitions,
            key_serdes_type=key_serdes_type,
            value_serdes_type=value_serdes_type,
            partitioner_type=partitioner_type,
            **kwargs,
        )
        table.create_meta(**kwargs)
        return table

    @staticmethod
    def meta_table_name(name):
        return f"{name}.meta"

    def get_table(self, name, namespace):
        meta = StorageTableMeta(name=name, namespace=namespace)
        if meta and meta.exists():
            table = self.load(
                name=meta.get_name(),
                namespace=meta.get_namespace(),
                address=meta.get_address(),
                partitions=meta.get_partitions(),
                store_type=meta.get_store_type(),
                options=meta.get_options(),
            )
            table.meta = meta
            return table
        else:
            return None

    @classmethod
    def get_table_meta(cls, name, namespace):
        meta = StorageTableMeta(name=name, namespace=namespace)
        if meta and meta.exists():
            return meta
        else:
            return None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.destroy()

    def destroy(self):
        try:
            self.stop()
        except Exception as e:
            LOGGER.warning(
                f"stop storage session {self._session_id} failed, try to kill", e
            )
            self.kill()

    def table(
        self,
        name,
        namespace,
        address,
        partitions,
        key_serdes_type,
        value_serdes_type,
        partitioner_type,
        store_type,
        options,
        **kwargs,
    ):
        raise NotImplementedError()

    def load(
        self,
        name,
        namespace,
        address,
        store_type,
        partitions,
        **kwargs,
    ):
        raise NotImplementedError()

    def stop(self):
        raise NotImplementedError()

    def kill(self):
        raise NotImplementedError()

    @property
    def session_id(self):
        return self._session_id

    @property
    def engine(self):
        return self._engine


class Session(object):
    __GLOBAL_SESSION = None

    @classmethod
    def get_global(cls):
        return cls.__GLOBAL_SESSION

    @classmethod
    def _as_global(cls, sess):
        cls.__GLOBAL_SESSION = sess

    def as_global(self):
        self._as_global(self)
        return self

    def __init__(self, session_id: str = None, options=None):
        if options is None:
            options = {}
        self._storage_engine = ENGINES.get(EngineType.STORAGE, None)
        self._storage_session: typing.Dict[StorageSessionABC] = {}
        self._session_id = str(uuid.uuid1()) if not session_id else session_id
        self._logger = (
            LOGGER
            if options.get("logger", None) is None
            else options.get("logger", None)
        )

        self._logger.info(f"create manager session {self._session_id}")

    @property
    def session_id(self) -> str:
        return self._session_id

    def _open(self):
        return self

    def _close(self):
        self.destroy_all_sessions()

    def __enter__(self):
        return self._open()

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_tb:
            self._logger.exception("", exc_info=(exc_type, exc_val, exc_tb))
        return self._close()

    def _get_or_create_storage(
        self,
        storage_session_id=None,
        storage_engine=None,
        record: bool = True,
        **kwargs,
    ) -> StorageSessionABC:
        storage_session_id = (
            f"{self._session_id}_storage_{uuid.uuid1()}"
            if not storage_session_id
            else storage_session_id
        )

        if storage_session_id in self._storage_session:
            return self._storage_session[storage_session_id]
        else:
            if storage_engine is None:
                storage_engine = self._storage_engine

        for session in self._storage_session.values():
            if storage_engine == session.engine:
                return session

        if record:
            self.save_record(
                engine_type=EngineType.STORAGE,
                engine_name=storage_engine,
                engine_session_id=storage_session_id,
            )

        if storage_engine == StorageEngine.EGGROLL:
            from fate_flow.engine.storage.eggroll import StorageSession

        elif storage_engine == StorageEngine.STANDALONE:
            from fate_flow.engine.storage.standalone import StorageSession

        elif storage_engine == StorageEngine.FILE:
            from fate_flow.engine.storage.file import StorageSession

        elif storage_engine == StorageEngine.HDFS:
            from fate_flow.engine.storage.hdfs import StorageSession

        else:
            raise NotImplementedError(
                f"can not be initialized with storage engine: {storage_engine}"
            )
        storage_session = StorageSession(
            session_id=storage_session_id, options=kwargs.get("options", {})
        )

        self._storage_session[storage_session_id] = storage_session

        return storage_session

    def get_table(
        self, name, namespace, ignore_disable=False
    ) -> typing.Union[StorageTableABC, None]:
        meta = Session.get_table_meta(name=name, namespace=namespace)
        if meta is None:
            return None
        if meta.get_disable() and not ignore_disable:
            raise Exception(f"table {namespace} {name} disable: {meta.get_disable()}")
        engine = meta.get_engine()
        storage_session = self._get_or_create_storage(storage_engine=engine)
        table = storage_session.get_table(name=name, namespace=namespace)
        return table

    @classmethod
    def get_table_meta(cls, name, namespace) -> typing.Union[StorageTableMetaABC, None]:
        meta = StorageSessionBase.get_table_meta(name=name, namespace=namespace)
        return meta

    def storage(self, **kwargs):
        return self._get_or_create_storage(**kwargs)

    @DB.connection_context()
    def save_record(self, engine_type, engine_name, engine_session_id):
        self._logger.info(
            f"try to save session record for manager {self._session_id}, {engine_type} {engine_name} {engine_session_id}"
        )
        session_record = SessionRecord()
        session_record.f_manager_session_id = self._session_id
        session_record.f_engine_type = engine_type
        session_record.f_engine_name = engine_name
        session_record.f_engine_session_id = engine_session_id
        # TODO: engine address
        session_record.f_engine_address = {}
        session_record.f_create_time = base_utils.current_timestamp()
        msg = f"save storage session record for manager {self._session_id}, {engine_type} {engine_name} {engine_session_id}"
        try:
            effect_count = session_record.save(force_insert=True)
            if effect_count != 1:
                raise RuntimeError(f"{msg} failed")
        except peewee.IntegrityError as e:
            LOGGER.warning(e)
        except Exception as e:
            raise RuntimeError(f"{msg} exception", e)
        self._logger.info(
            f"save session record for manager {self._session_id}, {engine_type} {engine_name} {engine_session_id} successfully"
        )

    @DB.connection_context()
    def delete_session_record(self, engine_session_id):
        rows = (
            SessionRecord.delete()
            .where(SessionRecord.f_engine_session_id == engine_session_id)
            .execute()
        )
        if rows > 0:
            self._logger.info(f"delete session {engine_session_id} record successfully")
        else:
            self._logger.warning(f"delete session {engine_session_id} record failed")

    @classmethod
    @DB.connection_context()
    def query_sessions(cls, reverse=None, order_by=None, **kwargs):
        return SessionRecord.query(reverse=reverse, order_by=order_by, **kwargs)

    @DB.connection_context()
    def get_session_from_record(self, **kwargs):
        self._logger.info(f"query by manager session id {self._session_id}")
        session_records = self.query_sessions(
            manager_session_id=self._session_id, **kwargs
        )
        self._logger.info(
            [session_record.f_engine_session_id for session_record in session_records]
        )
        for session_record in session_records:
            try:
                engine_session_id = session_record.f_engine_session_id
                if session_record.f_engine_type == EngineType.STORAGE:
                    self._get_or_create_storage(
                        storage_session_id=engine_session_id,
                        storage_engine=session_record.f_engine_name,
                        record=False,
                    )
            except Exception as e:
                self._logger.error(e)
                self.delete_session_record(
                    engine_session_id=session_record.f_engine_session_id
                )

    def destroy_all_sessions(self, **kwargs):
        self._logger.info(
            f"start destroy manager session {self._session_id} all sessions"
        )
        self.get_session_from_record(**kwargs)
        self.destroy_storage_session()
        self._logger.info(
            f"finish destroy manager session {self._session_id} all sessions"
        )

    def destroy_storage_session(self):
        for session_id, session in self._storage_session.items():
            try:
                self._logger.info(f"try to destroy storage session {session_id}")
                session.destroy()
                self._logger.info(f"destroy storage session {session_id} successfully")
            except Exception as e:
                self._logger.exception(
                    f"destroy storage session {session_id} failed", e
                )
            self.delete_session_record(engine_session_id=session_id)


def get_session() -> Session:
    return Session.get_global()
