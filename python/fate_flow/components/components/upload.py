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
import os
import secrets
from typing import Union

from fate_flow.components import cpn
from fate_flow.engine.storage import Session, StorageEngine, DataType, StorageTableMeta
from fate_flow.entity.spec.dag import ArtifactSource
from fate_flow.manager.outputs.data import DatasetManager
from fate_flow.runtime.system_settings import STANDALONE_DATA_HOME
from fate_flow.utils.file_utils import get_fate_flow_directory


@cpn.component()
def upload(
    config
):
    upload_data(config)


def upload_data(config):
    job_id = config.pop("job_id")
    upload_object = Upload()
    data = upload_object.run(
        parameters=UploadParam(
            **config
        ),
        job_id=job_id
    )


class Param(object):
    def to_dict(self):
        d = {}
        for k, v in self.__dict__.items():
            if v is None:
                continue
            d[k] = v
        return d


class MetaParam(Param):
    def __init__(
            self,
            sample_id_name: str = None,
            match_id_name: str = None,
            match_id_list: list = None,
            match_id_range: int = 0,
            label_name: Union[None, str] = None,
            label_type: str = "int32",
            weight_name: Union[None, str] = None,
            weight_type: str = "float32",
            header: str = None,
            delimiter: str = ",",
            dtype: Union[str, dict] = "float32",
            na_values: Union[str, list, dict] = None,
            input_format: str = "dense",
            tag_with_value: bool = False,
            tag_value_delimiter: str = ":"
    ):
        self.sample_id_name = sample_id_name
        self.match_id_name = match_id_name
        self.match_id_list = match_id_list
        self.match_id_range = match_id_range
        self.label_name = label_name
        self.label_type = label_type
        self.weight_name = weight_name
        self.weight_type = weight_type
        self.header = header
        self.delimiter = delimiter
        self.dtype = dtype
        self.na_values = na_values
        self.input_format = input_format
        self.tag_with_value = tag_with_value
        self.tag_value_delimiter = tag_value_delimiter


class UploadParam(Param):
    def __init__(
            self,
            namespace="",
            name="",
            file="",
            storage_engine="",
            head=1,
            partitions=10,
            extend_sid=False,
            is_temp_file=False,
            address: dict = {},
            meta: dict = {}
    ):
        self.name = name
        self.namespace = namespace
        self.file = file
        self.storage_engine = storage_engine
        self.head = head
        self.partitions = partitions
        self.extend_sid = extend_sid
        self.meta = MetaParam(**meta)
        self.storage_address = address
        self.is_temp_file = is_temp_file


class Upload:
    def __init__(self):
        self.parameters = None
        self.table = None
        self.data_meta = {}

    def run(self, parameters: UploadParam, job_id=""):
        self.parameters = parameters
        logging.info(self.parameters.to_dict())
        storage_address = self.parameters.storage_address
        if not os.path.isabs(parameters.file):
            parameters.file = os.path.join(
                get_fate_flow_directory(), parameters.file
            )
        name, namespace = parameters.name, parameters.namespace
        with Session() as sess:
            # clean table
            table = sess.get_table(namespace=namespace, name=name)
            if table:
                logging.info(
                    f"destroy table name: {name} namespace: {namespace} engine: {table.engine}"
                )
                try:
                    table.destroy()
                except Exception as e:
                    logging.error(e)
            else:
                logging.info(
                    f"can not found table name: {name} namespace: {namespace}, pass destroy"
                )
            address_dict = storage_address.copy()
            storage_engine = self.parameters.storage_engine
            storage_session = sess.storage(
                storage_engine=storage_engine
            )
            if storage_engine in {StorageEngine.EGGROLL, StorageEngine.STANDALONE}:
                upload_address = {
                    "name": name,
                    "namespace": namespace
                }
                if storage_engine == StorageEngine.STANDALONE:
                    upload_address.update({"home": STANDALONE_DATA_HOME})
            elif storage_engine in {StorageEngine.HDFS, StorageEngine.FILE}:
                upload_address = {
                    "path": DatasetManager.upload_data_path(
                        name=name,
                        namespace=namespace,
                        storage_engine=storage_engine
                    )
                }
            else:
                raise RuntimeError(f"can not support this storage engine: {storage_engine}")
            address_dict.update(upload_address)
            logging.info(f"upload to {storage_engine} storage, address: {address_dict}")
            address = StorageTableMeta.create_address(
                storage_engine=storage_engine, address_dict=address_dict
            )
            self.table = storage_session.create_table(
                address=address,
                source=ArtifactSource(
                    task_id="",
                    party_task_id="",
                    task_name="upload",
                    component="upload",
                    output_artifact_key="data"
                ).dict(),
                **self.parameters.to_dict()
            )
            data_table_count = self.save_data_table(job_id)
            logging.info("------------load data finish!-----------------")

            logging.info("file: {}".format(self.parameters.file))
            logging.info("total data_count: {}".format(data_table_count))
            logging.info("table name: {}, table namespace: {}".format(name, namespace))
            return {"name": name, "namespace": namespace, "count": data_table_count}

    def save_data_table(self, job_id):
        input_file = self.parameters.file
        input_feature_count = self.get_count(input_file)
        self.upload_file(input_file, job_id, input_feature_count)
        table_count = self.table.count()
        metas_info = {
            "count": table_count,
            "partitions": self.parameters.partitions,
            "data_type": DataType.TABLE
        }
        self.table.meta.update_metas(**metas_info)
        return table_count

    def update_schema(self, fp):
        id_index = 0
        read_status = False
        if self.parameters.head is True:
            data_head = fp.readline()
            id_index = self.update_table_meta(data_head)
            read_status = True
        else:
            pass
        return id_index, read_status

    def upload_file(self, input_file, job_id, input_feature_count=None, table=None):
        if not table:
            table = self.table
        part_of_data = []
        with open(input_file, "r") as fp:
            id_index, read_status = self.update_schema(fp)
            if read_status:
                input_feature_count -= 1
            self.table.put_all(self.kv_generator(input_feature_count, fp, job_id, part_of_data, id_index=id_index))
            table.meta.update_metas(part_of_data=part_of_data)

    def get_line(self):
        if not self.parameters.extend_sid:
            line = self.get_data_line
        else:
            line = self.get_sid_data_line
        return line

    @staticmethod
    def get_data_line(values, delimiter, id_index, **kwargs):
        if id_index:
            k = values[id_index]
            v = delimiter.join([
                delimiter.join(values[:id_index]),
                delimiter.join(values[id_index + 1:])
            ]).strip(delimiter)
        else:
            k = values[0]
            v = delimiter.join(list(map(str, values[1:])))
        return k, v

    @staticmethod
    def get_sid_data_line(values, delimiter, fate_uuid, line_index, **kwargs):
        return fate_uuid + str(line_index), delimiter.join(list(map(str, values[:])))

    def kv_generator(self, input_feature_count, fp, job_id, part_of_data, id_index):
        fate_uuid = secrets.token_bytes(16).hex()
        get_line = self.get_line()
        line_index = 0
        logging.info(input_feature_count)
        while True:
            lines = fp.readlines(104857600)
            if lines:
                for line in lines:
                    values = line.rstrip().split(self.parameters.meta.delimiter)
                    k, v = get_line(
                        values=values,
                        line_index=line_index,
                        delimiter=self.parameters.meta.delimiter,
                        fate_uuid=fate_uuid,
                        id_index=id_index
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
                logging.info(f"job info: {job_info}")
            else:
                return

    def get_count(self, input_file):
        with open(input_file, "r", encoding="utf-8") as fp:
            count = 0
            for line in fp:
                count += 1
        return count

    def update_table_meta(self, data_head):
        logging.info(f"data head: {data_head}")
        update_schema, id_index = self.get_header_schema(
            header_line=data_head
        )
        self.data_meta.update(self.parameters.meta.to_dict())
        self.data_meta.update(update_schema)
        self.table.meta.update_metas(data_meta=self.data_meta)
        return id_index

    def get_header_schema(self, header_line):
        delimiter = self.parameters.meta.delimiter
        sample_id_name = self.parameters.meta.sample_id_name
        sample_id_index = 0
        if self.parameters.extend_sid:
            sample_id_name = "extend_sid"
            header = delimiter.join([sample_id_name, header_line]).strip()
        else:
            header_list = header_line.split(delimiter)
            if not sample_id_name:
                # default set sample_id_index = 0
                sample_id_name = header_list[0]
            else:
                if sample_id_name not in header_line:
                    raise RuntimeError(f"No found sample id {sample_id_name} in header")
                sample_id_index = header_list.index(sample_id_name)
                if sample_id_index > 0:
                    header_line = self.join_in_index_line(delimiter, header_list, sample_id_index)
            header = header_line.strip()
        return {'header': header, "sample_id_name": sample_id_name}, sample_id_index

    @staticmethod
    def join_in_index_line(delimiter, values, id_index):
        return delimiter.join([
            values[id_index],
            delimiter.join(values[:id_index]),
            delimiter.join(values[id_index + 1:])
        ]).strip(delimiter)
