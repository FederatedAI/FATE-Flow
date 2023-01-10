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
import argparse
import json
import os
import time

from pydantic import typing

from fate_flow.engine.storage import Session, EggRollStoreType, StorageEngine, StorageTableMeta, StorageTableOrigin
from fate_flow.entity.engine_types import EngineType
from fate_flow.settings import ENGINES
from fate_flow.utils.file_utils import get_fate_flow_directory
from fate_flow.utils.log import getLogger

logger = getLogger("upload")

DEFAULT_ID_DELIMITER = ","
upload_block_max_bytes = 104857600


class Param(object):
    def to_dict(self):
        d = {}
        for k, v in self.__dict__.items():
            if v is None:
                continue
            d[k] = v
        return d


class MetaParam(Param):
    def __init__(self,
                 delimiter: str = ",",
                 label_name: typing.Union[None, str] = None,
                 label_type: str = "int",
                 weight_name: typing.Union[None, str] = None,
                 dtype: str = "float32",
                 input_format: str = "dense"):
        self.delimiter = delimiter
        self.label_name = label_name
        self.label_type = label_type
        self.weight_name = weight_name
        self.dtype = dtype
        self.input_format = input_format


class UploadParam(Param):
    def __init__(
            self,
            file="",
            head=1,
            partitions=10,
            namespace="",
            name="",
            storage_engine="",
            storage_address=None,
            destroy=False,
            meta=None
    ):
        self.file = file
        self.head = head
        self.delimiter = None
        self.partitions = partitions
        self.namespace = namespace
        self.name = name
        self.engine = storage_engine
        self.storage_address = storage_address
        self.destroy = destroy
        self.meta = MetaParam(**meta)


class Upload:
    def __init__(self):
        self.MAX_PARTITIONS = 1024
        self.MAX_BYTES = 1024 * 1024 * 8 * 500
        self.parameters: UploadParam = None
        self.table = None
        self.is_block = False
        self.session_id = None
        self.session = None
        self.schema = {}

    def run(self, parameters: UploadParam):
        self.parameters = parameters
        self.parameters.delimiter = self.parameters.meta.delimiter
        if not self.parameters.engine:
            self.parameters.engine = ENGINES.get(EngineType.STORAGE)
        logger.info(self.parameters.to_dict())
        storage_engine = parameters.engine
        storage_address = parameters.storage_address
        if not storage_address:
            storage_address = {}
        if not os.path.isabs(parameters.file):
            parameters.file = os.path.join(
                get_fate_flow_directory(), parameters.file
            )
        name, namespace = parameters.name, parameters.namespace
        read_head = parameters.head
        if read_head == 0:
            head = False
        elif read_head == 1:
            head = True
        else:
            raise Exception("'head' in conf.json should be 0 or 1")
        partitions = parameters.partitions
        if partitions <= 0 or partitions >= self.MAX_PARTITIONS:
            raise Exception(
                "Error number of partition, it should between %d and %d"
                % (0, self.MAX_PARTITIONS)
            )
        with Session() as sess:
            if self.parameters.destroy:
                table = sess.get_table(namespace=namespace, name=name)
                if table:
                    logger.info(
                        f"destroy table name: {name} namespace: {namespace} engine: {table.engine}"
                    )
                    try:
                        table.destroy()
                    except Exception as e:
                        logger.error(e)
                else:
                    logger.info(
                        f"can not found table name: {name} namespace: {namespace}, pass destroy"
                    )
            address_dict = storage_address.copy()
            storage_session = sess.storage(
                storage_engine=storage_engine
            )
            if storage_engine in {StorageEngine.EGGROLL, StorageEngine.STANDALONE}:
                upload_address = {
                    "name": name,
                    "namespace": namespace,
                    "storage_type": EggRollStoreType.ROLLPAIR_LMDB,
                }
            else:
                raise RuntimeError(f"can not support this storage engine: {storage_engine}")
            address_dict.update(upload_address)
            logger.info(f"upload to {storage_engine} storage, address: {address_dict}")
            address = StorageTableMeta.create_address(
                storage_engine=storage_engine, address_dict=address_dict
            )
            self.table = storage_session.create_table(address=address, origin=StorageTableOrigin.UPLOAD, **self.parameters.to_dict())

            data_table_count = self.save_data_table(head)

            self.table.meta.update_metas(in_serialized=True)
            logger.info("------------load data finish!-----------------")
            # rm tmp file
            logger.info("file: {}".format(self.parameters.file))
            logger.info("total data_count: {}".format(data_table_count))
            logger.info("table name: {}, table namespace: {}".format(name, namespace))
            return {"name": name, "namespace": namespace, "count": data_table_count}

    def save_data_table(self,  head=True):
        input_file = self.parameters.file
        input_feature_count = self.get_count(input_file)
        self.upload_file(input_file, head, input_feature_count)
        table_count = self.table.count()
        metas_info = {
            "count": table_count,
            "partitions": self.parameters.partitions
        }
        if self.parameters.meta:
            pass
        self.table.meta.update_metas(**metas_info)
        return table_count

    def upload_file(self, input_file, head, input_feature_count=None, table=None):
        if not table:
            table = self.table
        with open(input_file, "r") as fin:
            lines_count = 0
            if head is True:
                data_head = fin.readline()
                input_feature_count -= 1
                self.update_table_meta(data_head)
            n = 0
            line_index = 0
            while True:
                data = list()
                lines = fin.readlines(upload_block_max_bytes)
                logger.info(upload_block_max_bytes)
                if lines:
                    # self.append_data_line(lines, data, n)
                    for line in lines:
                        values = line.rstrip().split(self.parameters.delimiter)
                        k, v = self.get_data_line(
                            values=values,
                            delimiter=self.parameters.delimiter
                        )
                        data.append((k, v))
                        line_index += 1
                    lines_count += len(data)
                    table.put_all(data)
                else:
                    return
                n += 1

    def get_count(self, input_file):
        with open(input_file, "r", encoding="utf-8") as fp:
            count = 0
            for line in fp:
                count += 1
        return count

    def generate_table_name(self, input_file_path):
        str_time = time.strftime("%Y%m%d%H%M%S", time.localtime())
        file_name = input_file_path.split(".")[0]
        file_name = file_name.split("/")[-1]
        return file_name, str_time

    def update_table_meta(self, data_head):
        logger.info(f"data head: {data_head}")
        schema = self.get_header_schema(
            header_line=data_head,
            delimiter=self.parameters.delimiter
        )
        self.schema.update(schema)
        self.schema.update(self.parameters.meta.to_dict())
        self.table.put_meta([("schema", self.schema)])

    def get_header_schema(self, header_line, delimiter):
        header_source_item = header_line.split(delimiter)
        header = delimiter.join(header_source_item[1:]).strip()
        sid = header_source_item[0].strip()
        return {'header': header, 'sid': sid}

    def get_data_line(self, values, delimiter, **kwargs):
        return values[0], self.list_to_str(values[1:], delimiter=delimiter)

    @staticmethod
    def list_to_str(input_list, delimiter):
        return delimiter.join(list(map(str, input_list)))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', required=True, type=str, help="runtime conf path")
    args = parser.parse_args()
    path = args.config
    with open(args.config, "r") as f:
        conf = json.load(f)
        logger.info(conf)
    Upload().run(parameters=UploadParam(**conf))