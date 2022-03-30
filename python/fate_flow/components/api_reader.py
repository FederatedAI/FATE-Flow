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
import time
from contextlib import closing

import requests
from requests_toolbelt import MultipartEncoder

from fate_arch.common.data_utils import default_output_info
from fate_arch.session import Session
from fate_flow.components._base import ComponentMeta, BaseParam, ComponentBase, ComponentInputProtocol
from fate_flow.entity import Metric
from fate_flow.settings import TEMP_DIRECTORY
from fate_flow.utils.data_utils import convert_output
from fate_flow.utils.log_utils import getLogger
from fate_flow.utils.upload_utils import UploadFile

logger = getLogger()
api_reader_cpn_meta = ComponentMeta("ApiReader")


@api_reader_cpn_meta.bind_param
class ApiReaderParam(BaseParam):
    def __init__(self, adapter, method, url, header, body, timeout=60*60*8):
        pass

    def check(self):
        return True


@api_reader_cpn_meta.bind_runner.on_guest.on_host
class ApiReader(ComponentBase):
    def __init__(self):
        super(ApiReader, self).__init__()
        self.parameters = {}

    def _run(self, cpn_input: ComponentInputProtocol):
        self.cpn_input = cpn_input
        self.parameters = cpn_input.parameters
        self.task_dir = os.path.join(TEMP_DIRECTORY, self.tracker.task_id, str(self.tracker.task_version))
        self.table = None
        logger.info(f"parameters: {self.parameters}")
        self.request = getattr(requests, self.parameters.get("method", "post").lower(), None)
        if self.parameters.get("address"):
            self.request_address = self.parameters.get("address")
        else:
            self.request_address = "http://{}:{}".format(ip, port)
        logger.info(f"request address: {self.request_address}")
        response = self.upload_data()
        logger.info(f"upload response: {response.text}")
        if response.status_code == 200:
            response_data = response.json()
            if response_data.get("code") == 0:
                logger.info(f"request success, start check status")
                status = self.check_status(response_data.get("id"))
                if status:
                    download_path = self.download_data(response_data.get("id"))
                    table, output_name, output_namespace = self.output_feature_table()
                    count = UploadFile.upload(
                        download_path,
                        head=self.parameters.get("head"),
                        table=table,
                        id_delimiter=","
                    )

                    self.tracker.log_output_data_info(
                        data_name="",
                        table_namespace=output_namespace,
                        table_name=output_name,
                    )
                    self.tracker.log_metric_data(
                        metric_namespace="api_reader",
                        metric_name="upload",
                        metrics=[Metric("count", count)],
                    )

    def output_feature_table(self):
        (
            output_name,
            output_namespace
        ) = default_output_info(
            task_id=self.tracker.task_id,
            task_version=self.tracker.task_version,
            output_type="data"
        )
        input_table_info = self.cpn_input.flow_feeded_parameters.get("table_info")[0]
        _, output_table_address, output_table_engine = convert_output(
            input_table_info["namespace"],
            input_table_info["name"],
            output_name,
            output_namespace, self.table.engine
        )
        sess = Session.get_global()
        output_table_session = sess.storage(storage_engine=output_table_engine)
        table = output_table_session.create_table(
            address=output_table_address,
            name=output_name,
            namespace=output_namespace,
            partitions=self.table.partitions,
        )
        return table, output_name, output_namespace

    def check_status(self, job_id):
        for i in range(0, self.parameters.get("timeout", 60 * 60 * 8)):
            status_response = self.request(
                url=self.parameters.get("status_url"),
                json={"id": job_id}
            )
            logger.info(f"status: {status_response.text}")
            if status_response.status_code == 200 and status_response.json.get("status") == "success":
                logger.info(f"id {job_id} status success, start download")
                return True
            time.sleep(1)
        raise TimeoutError("check status timeout")

    def download_data(self, job_id):
        download_path = os.path.join(self.task_dir, "features")
        with closing(self.request(url=self.parameters.get("download"), json={"id": job_id}, stream=True)) as response:
            if response.status_code == 200:
                with open(download_path, 'wb') as fw:
                    for chunk in response.iter_content(1024):
                        if chunk:
                            fw.write(chunk)
        return download_path

    def upload_data(self):
        id_path = os.path.join(self.task_dir, "id")
        logger.info(f"save to: {id_path}")
        with open(id_path, "w") as f:
            for k, _ in self.table.collect():
                f.write(f"{k}\n")
            data = MultipartEncoder(
                fields={'file': (id_path, f, 'application/octet-stream')}
            )
            response = self.request(
                url=os.path.join(self.request_address, self.parameters.get("upload")),
                params=self.parameters.get("body", {}),
                data=data,
                headers={'Content-Type': data.content_type}
            )
        return response
