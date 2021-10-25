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

from fate_flow.utils.log_utils import getLogger
from fate_arch.session import Session
from fate_arch.storage import DEFAULT_ID_DELIMITER
from fate_flow.components._base import (
    BaseParam,
    ComponentBase,
    ComponentMeta,
    ComponentInputProtocol,
)
from fate_flow.entity import Metric, MetricMeta
from fate_flow.scheduling_apps.client import ControllerClient
from fate_flow.utils import job_utils

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
        name, namespace = self.parameters.get("name"), self.parameters.get("namespace")
        with open(os.path.abspath(self.parameters["output_path"]), "w") as fw:
            session = Session(
                job_utils.generate_session_id(
                    self.tracker.task_id,
                    self.tracker.task_version,
                    self.tracker.role,
                    self.tracker.party_id,
                )
            )
            data_table = session.get_table(name=name, namespace=namespace)
            if not data_table:
                raise Exception(f"no found table {name} {namespace}")
            count = data_table.count()
            LOGGER.info("===== begin to export data =====")
            lines = 0
            job_info = {}
            job_info["job_id"] = self.tracker.job_id
            job_info["role"] = self.tracker.role
            job_info["party_id"] = self.tracker.party_id
            for key, value in data_table.collect():
                if not value:
                    fw.write(key + "\n")
                else:
                    fw.write(
                        key + self.parameters.get("delimiter", ",") + str(value) + "\n"
                    )
                lines += 1
                if lines % 2000 == 0:
                    LOGGER.info("===== export {} lines =====".format(lines))
                if lines % 10000 == 0:
                    job_info["progress"] = lines / count * 100 // 1
                    ControllerClient.update_job(job_info=job_info)
            job_info["progress"] = 100
            ControllerClient.update_job(job_info=job_info)
            self.callback_metric(
                metric_name="data_access",
                metric_namespace="download",
                metric_data=[Metric("count", data_table.count())],
            )
            LOGGER.info("===== export {} lines totally =====".format(lines))
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
