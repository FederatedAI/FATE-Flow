#!/usr/bin/env python
# -*- coding: utf-8 -*-
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
from fate_arch.common import log
from fate_arch.common.data_utils import default_output_info, default_output_fs_path
from fate_arch.session import Session
from fate_arch.storage import StorageEngine, StorageTableMeta
from fate_flow.components._base import (
    BaseParam,
    ComponentBase,
    ComponentInputProtocol,
    ComponentMeta,
)
from fate_flow.entity import Metric
from fate_flow.manager.data_manager import TableStorage, DataTableTracker

LOGGER = log.getLogger()

writer_cpn_meta = ComponentMeta("Writer")


@writer_cpn_meta.bind_param
class WriterParam(BaseParam):
    def __init__(self,
                 table_name=None,
                 namespace=None,
                 storage_engine=None,
                 address=None,
                 output_table_name=None,
                 output_namespace=None,
                 partitions=None):
        self.table_name = table_name
        self.namespace = namespace
        self.storage_engine = storage_engine
        self.address = address
        self.output_table_name = output_table_name
        self.output_namespace = output_namespace
        self.partitions = partitions

    def check(self):
        return True


@writer_cpn_meta.bind_runner.on_guest.on_host.on_local
class Writer(ComponentBase):
    def __init__(self):
        super(Writer, self).__init__()
        self.parameters = None
        self.job_parameters = None

    def _run(self, cpn_input: ComponentInputProtocol):
        self.parameters = cpn_input.parameters
        if self.parameters.get("namespace") and self.parameters.get("table_name"):
            namespace = self.parameters.get("namespace")
            name = self.parameters.get("table_name")
        elif cpn_input.flow_feeded_parameters.get("table_info"):
            namespace = cpn_input.flow_feeded_parameters.get("table_info")[0].get("namespace")
            name = cpn_input.flow_feeded_parameters.get("table_info")[0].get("name")
        else:
            raise Exception("no found name or namespace in input parameters")
        LOGGER.info(f"writer parameters:{self.parameters}")
        src_table = self._get_storage_table(namespace=namespace, name=name)
        output_name = self.parameters.get("output_table_name")
        output_namespace = self.parameters.get("output_namespace")
        if not output_namespace or not output_name:
            LOGGER.info("start create table info")
            output_namespace, output_name = self._create_output_table_info()
        LOGGER.info(f"output_namespace: {output_namespace}, output_name: {output_name}")
        engine = self.parameters.get("storage_engine").upper()
        dest_table = self._create_storage_table(engine=engine,
                                                address_dict=self.parameters.get("address"),
                                                name=output_name,
                                                namespace=output_namespace,
                                                partitions=self.parameters.get("partitions", src_table.meta.get_partitions()),
                                                id_delimiter=src_table.meta.get_id_delimiter() if src_table.meta.get_id_delimiter() else ",")

        _, dest_table.meta = dest_table.meta.update_metas(schema=src_table.meta.get_schema(),
                                                          id_delimiter=src_table.meta.get_id_delimiter() if src_table.meta.get_id_delimiter() else ',')

        count = TableStorage.copy_table(src_table, dest_table, deserialize_value=True)
        LOGGER.info("save success")
        # output table track
        DataTableTracker.create_table_tracker(
            output_name,
            output_namespace,
            entity_info={
                "have_parent": True,
                "parent_table_namespace": namespace,
                "parent_table_name": name,
                "job_id": self.tracker.job_id,
            },
        )
        self.tracker.log_output_data_info(
            data_name="writer",
            table_namespace=output_namespace,
            table_name=output_name,
        )
        self.tracker.log_metric_data(
            metric_namespace="writer",
            metric_name="writer",
            metrics=[Metric("output_table_name", output_name),
                     Metric("output_namespace", output_namespace),
                     Metric("count", count)],
        )


    @staticmethod
    def _get_storage_table(namespace, name):
        return Session.get_global().get_table(name=name, namespace=namespace)

    @staticmethod
    def _create_storage_table(engine, address_dict, name, namespace, partitions, id_delimiter):
        if not address_dict:
            address_dict = {}
        if engine == StorageEngine.MYSQL:
            if not address_dict.get("db") or not address_dict.get("name"):
                address_dict.update({"db": namespace, "name": name})

        elif engine == StorageEngine.EGGROLL:
            address_dict.update({"name": name, "namespace": namespace})

        elif engine == StorageEngine.STANDALONE:
            address_dict.update({"name": name, "namespace": namespace})

        elif engine == StorageEngine.HIVE:
            address_dict.update({"database": namespace, "name": f"{name}"})

        elif engine == StorageEngine.HDFS:
            if not address_dict.get("path"):
                address_dict.update({"path": default_output_fs_path(name=name, namespace=namespace, prefix=address_dict.get("path_prefix"))})
        elif engine == StorageEngine.LOCALFS:
            if not address_dict.get("path"):
                address_dict.update({"path": default_output_fs_path(name=name, namespace=namespace, storage_engine=StorageEngine.LOCALFS)})
        else:
            raise RuntimeError(f"{engine} storage is not supported")
        output_table_address = StorageTableMeta.create_address(
            storage_engine=engine, address_dict=address_dict
        )

        storage_session = Session.get_global().storage(storage_engine=engine)
        output_table = storage_session.create_table(
            address=output_table_address,
            name=name,
            namespace=namespace,
            partitions=partitions,
            id_delimiter=id_delimiter
        )
        return output_table

    def _create_output_table_info(self):
        (
            output_namespace,
            output_name
        ) = default_output_info(
            task_id=self.tracker.task_id,
            task_version=self.tracker.task_version,
            output_type="data"
        )
        return output_namespace, output_name




