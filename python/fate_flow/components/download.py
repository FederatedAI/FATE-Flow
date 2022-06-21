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
import os

from fate_arch import storage
from fate_flow.manager.data_manager import TableStorage
from fate_flow.utils.log_utils import getLogger
from fate_arch.storage import DEFAULT_ID_DELIMITER
from fate_flow.components._base import (
    BaseParam,
    ComponentBase,
    ComponentMeta,
    ComponentInputProtocol,
)
from fate_flow.entity import Metric, MetricMeta

LOGGER = getLogger()

download_cpn_meta = ComponentMeta("Download")


@download_cpn_meta.bind_param
class DownloadParam(BaseParam):
    def __init__(
        self,
        output_path="",
        delimiter=DEFAULT_ID_DELIMITER,
        namespace="",
        name="",
    ):
        self.output_path = output_path
        self.delimiter = delimiter
        self.namespace = namespace
        self.name = name

    def check(self):
        return True


@download_cpn_meta.bind_runner.on_local
class Download(ComponentBase):
    def __init__(self):
        super(Download, self).__init__()
        self.parameters = {}

    def _run(self, cpn_input: ComponentInputProtocol):
        self.parameters = cpn_input.parameters
        self.parameters["role"] = cpn_input.roles["role"]
        self.parameters["local"] = cpn_input.roles["local"]

        data_table_meta = storage.StorageTableMeta(name=self.parameters.get("name"), namespace=self.parameters.get("namespace"))
        TableStorage.send_table(
            output_tables_meta={"table": data_table_meta},
            output_data_file_path = os.path.abspath(self.parameters["output_path"]),
            local_download=True
        )
        self.callback_metric(
            metric_name="data_access",
            metric_namespace="download",
            metric_data=[Metric("count", data_table_meta.count)]
        )
        LOGGER.info("===== export {} lines totally =====".format(data_table_meta.count))
        LOGGER.info("===== export data finish =====")
        LOGGER.info(
            "===== export data file path:{} =====".format(
                os.path.abspath(self.parameters["output_path"])
            )
        )

    def callback_metric(self, metric_name, metric_namespace, metric_data):
        self.tracker.log_metric_data(
            metric_name=metric_name,
            metric_namespace=metric_namespace,
            metrics=metric_data,
        )
        self.tracker.set_metric_meta(
            metric_namespace,
            metric_name,
            MetricMeta(name="download", metric_type="DOWNLOAD"),
        )
