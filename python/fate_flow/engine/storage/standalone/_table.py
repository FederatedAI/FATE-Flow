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
from typing import Iterable

from fate_flow.engine.storage import (
    StandaloneStoreType,
    StorageEngine,
    StorageTableBase,
)
from fate_flow.engine.storage.standalone._standalone import Session


class StorageTable(StorageTableBase):
    def __init__(
        self,
        session: Session,
        table,
        key_serdes_type,
        value_serdes_type,
        partitioner_type,
        address=None,
        name: str = None,
        namespace: str = None,
        partitions: int = 1,
        store_type: StandaloneStoreType = StandaloneStoreType.ROLLPAIR_LMDB,
        options=None,
    ):
        super(StorageTable, self).__init__(
            name=name,
            namespace=namespace,
            address=address,
            partitions=partitions,
            options=options,
            engine=StorageEngine.STANDALONE,
            key_serdes_type=key_serdes_type,
            value_serdes_type=value_serdes_type,
            partitioner_type=partitioner_type,
        )
        self._store_type = store_type
        self._session = session
        self._table = table

    def _put_all(self, kv_list: Iterable, partitioner, **kwargs):
        return self._table.put_all(kv_list, partitioner)

    def _collect(self, **kwargs):
        return self._table.collect(**kwargs)

    def _count(self):
        return self._table.count()

    def _destroy(self):
        self._table.destroy()
