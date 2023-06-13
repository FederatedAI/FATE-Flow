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
import logging as logger
import os
import time
import uuid

from pydantic import typing

from fate_flow.engine.storage import Session, EggRollStoreType, StorageEngine, StorageTableMeta, StorageTableOrigin
from fate_flow.entity.types import EngineType
from fate_flow.runtime.system_settings import ENGINES
from fate_flow.utils.file_utils import get_fate_flow_directory


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
            extend_sid=False,
            destroy=False,
            meta=None,
            delimiter=","
    ):
        self.file = file
        self.head = head
        self.delimiter = delimiter
        self.partitions = partitions
        self.namespace = namespace
        self.name = name
        self.engine = storage_engine
        self.storage_address = storage_address
        self.extend_sid = extend_sid
        self.destroy = destroy
        self.meta = MetaParam(**meta)


class Upload:
    def __init__(self):
        self.MAX_PARTITIONS = 1024
        self.parameters: UploadParam
        self.table = None
        self.schema = {}

    def run(self, parameters: UploadParam, job_id=""):
        self.parameters = parameters
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
        with Session() as sess:
            if self.parameters.destroy:
                # clean table
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

            data_table_count = self.save_data_table(job_id)

            self.table.meta.update_metas(in_serialized=True)
            logger.info("------------load data finish!-----------------")
            # rm tmp file
            logger.info("file: {}".format(self.parameters.file))
            logger.info("total data_count: {}".format(data_table_count))
            logger.info("table name: {}, table namespace: {}".format(name, namespace))
            return {"name": name, "namespace": namespace, "count": data_table_count}

    def save_data_table(self, job_id):
        input_file = self.parameters.file
        input_feature_count = self.get_count(input_file)
        self.upload_file(input_file, job_id, input_feature_count)
        table_count = self.table.count()
        metas_info = {
            "count": table_count,
            "partitions": self.parameters.partitions
        }
        if self.parameters.meta:
            pass
        self.table.meta.update_metas(**metas_info)
        return table_count

    def update_schema(self, fp):
        read_status = False
        if self.parameters.head is True:
            data_head = fp.readline()
            self.update_table_meta(data_head)
            read_status = True
        else:
            # self.update_table_schema()
            pass
        return read_status

    def upload_file(self, input_file, job_id, input_feature_count=None, table=None):
        if not table:
            table = self.table
        part_of_data = []
        with open(input_file, "r") as fp:
            if self.update_schema(fp):
                input_feature_count -= 1
            self.table.put_all(self.kv_generator(input_feature_count, fp, job_id, part_of_data))
            table.meta.update_metas(part_of_data=part_of_data)

    def get_line(self):
        if not self.parameters.extend_sid:
            line = self.get_data_line
        else:
            line = self.get_sid_data_line
        return line

    @staticmethod
    def get_data_line(values, delimiter, **kwargs):
        return values[0], delimiter.join(list(map(str, values[1:])))

    @staticmethod
    def get_sid_data_line(values, delimiter, fate_uuid, line_index):
        return fate_uuid + str(line_index), delimiter.join(list(map(str, values[1:])))

    def kv_generator(self, input_feature_count, fp, job_id, part_of_data):
        fate_uuid = uuid.uuid1().hex
        get_line = self.get_line()
        line_index = 0
        logger.info(input_feature_count)
        while True:
            lines = fp.readlines(104857600)
            if lines:
                for line in lines:
                    values = line.rstrip().split(self.parameters.delimiter)
                    k, v = get_line(
                        values=values,
                        line_index=line_index,
                        delimiter=self.parameters.delimiter,
                        fate_uuid=fate_uuid,
                    )
                    yield k, v
                    line_index += 1
                    if line_index <= 100:
                        part_of_data.append((k, v))
                save_progress = line_index / input_feature_count * 100 // 1
                job_info = {
                    "progress": save_progress,
                    "job_id": job_id,
                    "role": "local",
                    "party_id": 0,
                }
                # ControllerClient.update_job(job_info=job_info)
                logger.info(f"job info: {job_info}")
            else:
                return

    def get_count(self, input_file):
        with open(input_file, "r", encoding="utf-8") as fp:
            count = 0
            for line in fp:
                count += 1
        return count

    def update_table_meta(self, data_head):
        logger.info(f"data head: {data_head}")
        schema = self.get_header_schema(
            header_line=data_head,
            delimiter=self.parameters.delimiter
        )
        self.schema.update(schema)
        self.schema.update(self.parameters.meta.to_dict())
        self.table.meta.update_metas(schema=schema)

    def get_header_schema(self, header_line, delimiter):
        header_source_item = header_line.split(delimiter)
        if self.parameters.extend_sid:
            header = delimiter.join(header_source_item).strip()
            sid = "extend_sid"
        else:
            header = delimiter.join(header_source_item[1:]).strip()
            sid = header_source_item[0].strip()
        return {'header': header, 'sid': sid}
