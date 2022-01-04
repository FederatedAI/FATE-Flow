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
from fate_arch.common.data_utils import default_output_fs_path
from fate_arch.session import Session
from fate_arch.storage import StorageEngine
from fate_flow.components._base import (
    BaseParam,
    ComponentBase,
    ComponentInputProtocol,
    ComponentMeta,
)
from fate_flow.entity import Metric
from fate_flow.external.data_storage import save_data_to_external_storage
from fate_flow.manager.data_manager import DataTableTracker

LOGGER = log.getLogger()

writer_cpn_meta = ComponentMeta("Writer")


@writer_cpn_meta.bind_param
class WriterParam(BaseParam):
    def __init__(self,
                 name=None,
                 namespace=None,
                 storage_engine=None,
                 address=None,
                 output_name=None,
                 output_namespace=None):
        self.name = name
        self.namespace = namespace
        self.storage_engine = storage_engine
        self.address = address
        self.output_name = output_name
        self.output_namespace = output_namespace

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
        if self.parameters.get("namespace") and self.parameters.get("name"):
            namespace = self.parameters.get("namespace")
            name = self.parameters.get("name")
        elif cpn_input.flow_feeded_parameters.get("table_info"):
            namespace = cpn_input.flow_feeded_parameters.get("table_info")[0].get("namespace")
            name = cpn_input.flow_feeded_parameters.get("table_info")[0].get("name")
        else:
            raise Exception("no found name or namespace in input parameters")
        LOGGER.info(f"writer parameters:{self.parameters}")
        src_table = Session.get_global().get_table(name=name, namespace=namespace)
        output_name = self.parameters.get("output_name")
        output_namespace = self.parameters.get("output_namespace")
        engine = self.parameters.get("storage_engine")
        address_dict = self.parameters.get("address")

        if output_name and output_namespace:
            table_meta = src_table.meta.to_dict()
            address_dict = src_table.meta.get_address().__dict__
            engine = src_table.meta.get_engine()
            table_meta.update({
                "name": output_name,
                "namespace": output_namespace,
                "address": self._create_save_address(engine, address_dict, output_name, output_namespace),
            })
            src_table.save_as(**table_meta)
            # output table track
            DataTableTracker.create_table_tracker(
                name,
                namespace,
                entity_info={
                    "have_parent": True,
                    "parent_table_namespace": namespace,
                    "parent_table_name": name,
                    "job_id": self.tracker.job_id,
                }
            )

        elif engine and address_dict:
            save_data_to_external_storage(engine, address_dict, src_table)

        LOGGER.info("save success")
        self.tracker.log_output_data_info(
            data_name="writer",
            table_namespace=output_namespace,
            table_name=output_name,
        )
        self.tracker.log_metric_data(
            metric_namespace="writer",
            metric_name="writer",
            metrics=[Metric("count", src_table.meta.get_count()),
                     Metric("storage_engine", engine)]
        )

    @staticmethod
    def _create_save_address(engine, address_dict, name, namespace):
        if engine == StorageEngine.EGGROLL:
            address_dict.update({"name": name, "namespace": namespace})

        elif engine == StorageEngine.STANDALONE:
            address_dict.update({"name": name, "namespace": namespace})

        elif engine == StorageEngine.HIVE:
            address_dict.update({"database": namespace, "name": f"{name}"})

        elif engine == StorageEngine.HDFS:
            address_dict.update({"path": default_output_fs_path(name=name,
                                                                namespace=namespace,
                                                                prefix=address_dict.get("path_prefix"))})
        elif engine == StorageEngine.LOCALFS:
            address_dict.update({"path": default_output_fs_path(name=name, namespace=namespace,
                                                                storage_engine=StorageEngine.LOCALFS)})
        else:
            raise RuntimeError(f"{engine} storage is not supported")
        return address_dict
