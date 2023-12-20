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
import logging

from fate_flow.components import cpn
from fate_flow.engine import storage
from fate_flow.entity.spec.dag import IOMeta, ArtifactOutputSpec, Metadata, TaskConfigSpec
from fate_flow.errors.server_error import NoFoundTable
from fate_flow.manager.outputs.data import DataManager


@cpn.component()
def download(
    config,
    outputs: IOMeta.OutputMeta
):
    download_data(config, outputs)


def download_data(config: TaskConfigSpec, outputs: IOMeta.OutputMeta):
    parameters = config.parameters
    download_object = Download()
    download_object.run(
        parameters=DownloadParam(
            **parameters
        ),
        outputs=outputs
    )


class DownloadParam(object):
    def __init__(
            self,
            namespace,
            name,
            path,
    ):
        self.name = name
        self.namespace = namespace
        self.path = path


class Download:
    def __init__(self):
        self.parameters = None
        self.table = None
        self.data_meta = {}

    def run(self, parameters: DownloadParam, outputs: IOMeta.OutputMeta):
        data_table_meta = storage.StorageTableMeta(name=parameters.name, namespace=parameters.namespace)
        if not data_table_meta:
            raise NoFoundTable(name=parameters.name, namespace=parameters.namespace)
        download_dir = parameters.path
        logging.info("start download data")
        DataManager.send_table(
            output_tables_meta={"data": data_table_meta},
            download_dir=download_dir
        )
        outputs.data = {"output_data": ArtifactOutputSpec(
            uri="",
            metadata=Metadata(namespace=parameters.namespace, name=parameters.name),
            type_name=data_table_meta.data_type,
        ).dict()}
        logging.info(f"download data success, download path: {parameters.path}")
