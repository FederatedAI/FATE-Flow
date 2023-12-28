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

from fate_flow.engine import storage
from fate_flow.manager.outputs.data import DataManager


class Param(object):
    def to_dict(self):
        d = {}
        for k, v in self.__dict__.items():
            if v is None:
                continue
            d[k] = v
        return d


class DownloadParam(Param):
    def __init__(
            self,
            dir_name="",
            namespace="",
            name=""
    ):
        self.dir_name = dir_name
        self.namespace = namespace
        self.name = name


class Download:
    def __init__(self):
        self.table = None
        self.schema = {}

    def run(self, parameters: DownloadParam, job_id=""):
        data_table_meta = storage.StorageTableMeta(
            name=parameters.name,
            namespace=parameters.namespace
        )
        DataManager.send_table(
            output_tables_meta={"table": data_table_meta},
            download_dir=os.path.abspath(parameters.dir_name)
        )

