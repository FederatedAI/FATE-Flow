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

from eggroll.session import session_init
from eggroll.computing import RollPairContext
from fate_flow.engine.storage import EggRollStoreType, StorageEngine, StorageSessionBase
from fate_flow.engine.storage.eggroll._table import StorageTable
from fate_flow.entity.types import EggRollAddress


class StorageSession(StorageSessionBase):
    def __init__(self, session_id, host: str = None, port: int = None, options=None, config_options=None, config_properties_file=None):
        super(StorageSession, self).__init__(
            session_id=session_id, engine=StorageEngine.EGGROLL
        )
        self._options = options if options else {}
        self._rp_session = session_init(
            session_id=self._session_id,
            host=host,
            port=port,
            options=self._options,
            config_options=config_options,
            config_properties_file=config_properties_file
        )
        self._rpc = RollPairContext(session=self._rp_session)
        self._session_id = self._rp_session.get_session_id()

    def load(
        self,
        name,
        namespace,
        address: EggRollAddress,
        store_type,
        partitions,
        options=None,
        **kwargs,
    ):
        if isinstance(address, EggRollAddress):
            _table = self._rpc.load_rp(
                namespace=address.namespace,
                name=address.name,
                store_type=store_type,
            )

            return StorageTable(
                context=self._rpc,
                table=_table,
                name=name,
                namespace=namespace,
                address=address,
                partitions=partitions,
                store_type=store_type,
                key_serdes_type=_table.get_store().key_serdes_type,
                value_serdes_type=_table.get_store().value_serdes_type,
                partitioner_type=_table.get_store().partitioner_type,
                options=options,
            )
        raise NotImplementedError(
            f"address type {type(address)} not supported with standalone storage"
        )

    def table(
        self,
        name,
        namespace,
        address,
        partitions,
        key_serdes_type,
        value_serdes_type,
        partitioner_type,
        store_type: str = EggRollStoreType.ROLLPAIR_LMDB,
        options=None,
        **kwargs,
    ):
        if isinstance(address, EggRollAddress):
            if options is None:
                options = {}
            _table = self._rpc.create_rp(
                id=-1,
                name=address.name,
                namespace=address.namespace,
                total_partitions=partitions,
                store_type=store_type,
                key_serdes_type=key_serdes_type,
                value_serdes_type=value_serdes_type,
                partitioner_type=partitioner_type,
                options=options,
            )

            return StorageTable(
                context=self._rpc,
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
            f"address type {type(address)} not supported with eggroll storage"
        )

    def cleanup(self, name, namespace):
        self._rpc.cleanup(name=name, namespace=namespace)

    def stop(self):
        return self._rp_session.stop()

    def kill(self):
        return self._rp_session.kill()
