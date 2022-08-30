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
import json
import os
import time
from contextlib import closing

import requests
from requests_toolbelt import MultipartEncoder

from fate_arch.common.data_utils import default_output_info
from fate_arch.session import Session
from fate_flow.components._base import ComponentMeta, BaseParam, ComponentBase, ComponentInputProtocol
from fate_flow.db.service_registry import ServiceRegistry
from fate_flow.entity import Metric
from fate_flow.settings import TEMP_DIRECTORY
from fate_flow.utils.data_utils import convert_output
from fate_flow.utils.log_utils import getLogger
from fate_flow.utils.upload_utils import UploadFile

logger = getLogger()
api_reader_cpn_meta = ComponentMeta("ApiReader")


@api_reader_cpn_meta.bind_param
class ApiReaderParam(BaseParam):
    def __init__(
            self,
            server_name=None,
            parameters=None,
            id_delimiter=",",
            head=True,
            extend_sid=False,
            timeout=60 * 60 * 8
    ):
        self.server_name = server_name
        self.parameters = parameters
        self.id_delimiter = id_delimiter
        self.head = head
        self.extend_sid = extend_sid
        self.time_out = timeout

    def check(self):
        return True


@api_reader_cpn_meta.bind_runner.on_guest.on_host
class ApiReader(ComponentBase):
    def __init__(self):
        super(ApiReader, self).__init__()
        self.parameters = {}
        self.required_url_key_list = ["upload", "query", "download"]
        self.service_info = {}

    def _run(self, cpn_input: ComponentInputProtocol):
        self.cpn_input = cpn_input
        self.parameters = cpn_input.parameters
        self.task_dir = os.path.join(TEMP_DIRECTORY, self.tracker.task_id, str(self.tracker.task_version))
        for cpn_name, data in cpn_input.datasets.items():
            for data_name, table_list in data.items():
                self.input_table = table_list[0]
        logger.info(f"parameters: {self.parameters}")
        if not self.parameters.get("server_name"):
            self._run_guest()
        else:
            self._run_host()

    def _run_guest(self):
        self.data_output = [self.input_table]

    def _run_host(self):
        self.set_service_registry_info()
        response = self.upload_data()
        logger.info(f"upload response: {response.text}")
        if response.status_code == 200:
            response_data = response.json()
            if response_data.get("code") == 0:
                logger.info(f"request success, start check status")
                job_id = response_data.get("data").get("jobId")
                status = self.check_status(job_id)
                if status:
                    download_path = self.download_data(job_id)
                    table, output_name, output_namespace = self.output_feature_table()
                    count = UploadFile.upload(
                        download_path,
                        head=self.parameters.get("head"),
                        table=table,
                        id_delimiter=self.parameters.get("id_delimiter"),
                        extend_sid=self.parameters.get("extend_sid")
                    )
                    table.meta.update_metas(count=count)
                    self.tracker.log_output_data_info(
                        data_name=self.cpn_input.flow_feeded_parameters.get("output_data_name")[0],
                        table_namespace=output_namespace,
                        table_name=output_name,
                    )
                    self.tracker.log_metric_data(
                        metric_namespace="api_reader",
                        metric_name="upload",
                        metrics=[Metric("count", count)],
                    )
        else:
            raise Exception(f"upload return: {response.text}")

    def output_feature_table(self):
        (
            output_name,
            output_namespace
        ) = default_output_info(
            task_id=self.tracker.task_id,
            task_version=self.tracker.task_version,
            output_type="data"
        )
        logger.info(f"flow_feeded_parameters: {self.cpn_input.flow_feeded_parameters}")
        input_table_info = self.cpn_input.flow_feeded_parameters.get("table_info")[0]
        _, output_table_address, output_table_engine = convert_output(
            input_table_info["name"],
            input_table_info["namespace"],
            output_name,
            output_namespace, self.input_table.engine
        )
        sess = Session.get_global()
        output_table_session = sess.storage(storage_engine=output_table_engine)
        table = output_table_session.create_table(
            address=output_table_address,
            name=output_name,
            namespace=output_namespace,
            partitions=self.input_table.partitions,
        )
        return table, output_name, output_namespace

    def check_status(self, job_id):
        query_registry_info = self.service_info.get("query")
        for i in range(0, self.parameters.get("timeout", 60 * 5)):
            status_response = getattr(requests, query_registry_info.f_method.lower(), None)(
                url=query_registry_info.f_url,
                json={"jobId": job_id}
            )
            logger.info(f"status: {status_response.text}")
            if status_response.status_code == 200 and status_response.json().get("data").get("status") == "success":
                logger.info(f"job id {job_id} status success, start download")
                return True
            logger.info(f"job id {job_id} status: {status_response.json().get('data').get('status')}")
            time.sleep(30)
        raise TimeoutError("check status timeout")

    def download_data(self, job_id):
        download_registry_info = self.service_info.get("download")
        download_path = os.path.join(self.task_dir, "features")
        logger.info(f"start download feature, url: {download_registry_info.f_url}")
        params = {"jobId": job_id}
        with closing(getattr(requests, download_registry_info.f_method.lower(), None)(
                url=download_registry_info.f_url,
                params={"requestBody": json.dumps(params)},
                stream=True)) as response:
            if response.status_code == 200:
                with open(download_path, 'wb') as fw:
                    for chunk in response.iter_content(1024):
                        if chunk:
                            fw.write(chunk)
            else:
                raise Exception(f"download return: {response.text}")
        return download_path

    def upload_data(self):
        id_path = os.path.join(self.task_dir, "id")
        logger.info(f"save to: {id_path}")
        os.makedirs(os.path.dirname(id_path), exist_ok=True)
        with open(id_path, "w") as f:
            for k, _ in self.input_table.collect():
                f.write(f"{k}\n")
            data = MultipartEncoder(
                fields={'file': (id_path, f, 'application/octet-stream')}
            )
            upload_registry_info = self.service_info.get("upload")
            logger.info(f"upload info:{upload_registry_info.to_dict()}")
            response = getattr(requests, upload_registry_info.f_method.lower(), None)(
                url=upload_registry_info.f_url,
                params={"requestBody": json.dumps(self.parameters.get("parameters", {}))},
                data=data,
                headers={'Content-Type': data.content_type}
            )
        return response

    def set_service_registry_info(self):
        for info in ServiceRegistry().load_service(server_name=self.parameters.get("server_name")):
            for key in self.required_url_key_list:
                if key == info.f_service_name:
                    self.service_info[key] = info
        logger.info(f"set service registry info:{self.service_info}")
