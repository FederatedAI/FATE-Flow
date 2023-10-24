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
from fate_flow.engine.storage import (
    StorageSessionBase,
    StorageEngine,
    StandaloneStoreType,
)
from fate_flow.engine.storage.standalone._table import StorageTable
from fate_flow.engine.storage.standalone._standalone import Session
from fate_flow.entity.types import AddressABC, StandaloneAddress
from fate_flow.runtime.system_settings import STANDALONE_DATA_HOME


class StorageSession(StorageSessionBase):
    def __init__(self, session_id, options=None):
        super(StorageSession, self).__init__(
            session_id=session_id, engine=StorageEngine.STANDALONE
        )
        self._options = options if options else {}
        self._session = Session(
            session_id=self._session_id, data_dir=STANDALONE_DATA_HOME
        )

    def load(
        self,
        name,
        namespace,
        address: AddressABC,
        store_type,
        partitions,
        options=None,
        **kwargs,
    ):
        if isinstance(address, StandaloneAddress):
            _table = self._session.load(
                namespace=address.namespace,
                name=address.name,
            )

            return StorageTable(
                session=self._session,
                table=_table,
                name=name,
                namespace=namespace,
                address=address,
                partitions=partitions,
                store_type=store_type,
                key_serdes_type=_table.key_serdes_type,
                value_serdes_type=_table.value_serdes_type,
                partitioner_type=_table.partitioner_type,
                options=options,
            )
        raise NotImplementedError(
            f"address type {type(address)} not supported with standalone storage"
        )

    def table(
        self,
        name,
        namespace,
        address: AddressABC,
        partitions,
        key_serdes_type,
        value_serdes_type,
        partitioner_type,
        store_type=None,
        options=None,
        **kwargs,
    ):
        if isinstance(address, StandaloneAddress):
            _table = self._session.create_table(
                namespace=address.namespace,
                name=address.name,
                partitions=partitions,
                need_cleanup=store_type == StandaloneStoreType.ROLLPAIR_IN_MEMORY,
                error_if_exist=False,
                key_serdes_type=key_serdes_type,
                value_serdes_type=value_serdes_type,
                partitioner_type=partitioner_type,
            )

            return StorageTable(
                session=self._session,
                table=_table,
                key_serdes_type=key_serdes_type,
                value_serdes_type=value_serdes_type,
                partitioner_type=partitioner_type,
                name=name,
                namespace=namespace,
                address=address,
                partitions=partitions,
                store_type=store_type,
                options=options,
            )
        raise NotImplementedError(
            f"address type {type(address)} not supported with standalone storage"
        )

    def cleanup(self, name, namespace):
        self._session.cleanup(name=name, namespace=namespace)

    def stop(self):
        self._session.stop()

    def kill(self):
        self._session.kill()
