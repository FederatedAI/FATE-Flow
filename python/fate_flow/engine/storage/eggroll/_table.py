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
from fate_flow.engine.storage import StorageTableBase, EggRollStoreType, StorageEngine
from eggroll.roll_pair.roll_pair import RollPairContext, RollPair


class StorageTable(StorageTableBase):
    def __init__(
        self,
        context: RollPairContext,
        table: RollPair,
        key_serdes_type,
        value_serdes_type,
        partitioner_type,
        name,
        namespace,
        address,
        partitions: int = 1,
        store_type: str = EggRollStoreType.ROLLPAIR_LMDB,
        options=None,
    ):
        self._context = context
        self._store_type = store_type
        self._table = table
        super(StorageTable, self).__init__(
            name=name,
            namespace=namespace,
            address=address,
            partitions=partitions,
            options=options,
            engine=StorageEngine.EGGROLL,
            key_serdes_type=key_serdes_type,
            value_serdes_type=value_serdes_type,
            partitioner_type=partitioner_type,
        )
        self._options["store_type"] = self._store_type
        self._options["total_partitions"] = partitions
        self._options["create_if_missing"] = True

    #
    # def _save_as(self, address, name, namespace, partitions=None, **kwargs):
    #     self._table.save_as(name=address.name, namespace=address.namespace)
    #     table = StorageTable(
    #         context=self._context,
    #         address=address,
    #         partitions=partitions,
    #         name=name,
    #         namespace=namespace,
    #     )
    #     return table

    def _put_all(self, kv_list: Iterable, partitioner, **kwargs):
        return self._table.put_all(kv_list, partitioner)

    def _collect(self, **kwargs) -> list:
        return self._table.get_all(**kwargs)

    def _destroy(self):
        self._table.destroy()

    def _count(self, **kwargs):
        return self._table.count()
