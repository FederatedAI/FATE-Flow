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
from fate_arch.session import Session
from fate_flow.components._base import (
    BaseParam,
    ComponentBase,
    ComponentInputProtocol,
    ComponentMeta,
)
from fate_flow.entity import Metric
from fate_flow.external.data_storage import save_data_to_external_storage

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
        src_table = Session.get_global().get_table(name=name, namespace=namespace)
        save_data_to_external_storage(self.parameters.get("storage_engine"), self.parameters.get("address"), src_table)
        LOGGER.info("save success")
        self.tracker.log_output_data_info(
            data_name="writer",
            table_namespace=namespace,
            table_name=name,
        )
        self.tracker.log_metric_data(
            metric_namespace="writer",
            metric_name="writer",
            metrics=[Metric("count", src_table.meta.get_count()),
                     Metric("storage_engine", self.parameters.get("storage_engine"))]
        )
