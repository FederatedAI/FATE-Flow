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
import json
import os
import pickle
import tarfile
import uuid
from tempfile import TemporaryDirectory

from flask import send_file

from fate_flow.engine import storage
from fate_flow.engine.storage import Session, StorageEngine, DataType
from fate_flow.entity.types import EggRollAddress, StandaloneAddress, HDFSAddress, PathAddress, ApiAddress
from fate_flow.errors.server_error import NoFoundTable
from fate_flow.manager.service.output_manager import OutputDataTracking
from fate_flow.runtime.system_settings import LOCALFS_DATA_HOME, STANDALONE_DATA_HOME, STORAGE
from fate_flow.utils import job_utils
from fate_flow.utils.io_utils import URI

DELIMITER = '\t'


class DataManager:
    @classmethod
    def send_table(
            cls,
            output_tables_meta,
            tar_file_name="",
            need_head=True,
            download_dir="",

    ):
        if not need_head:
            need_head = True
        output_data_file_list = []
        output_data_meta_file_list = []
        with TemporaryDirectory() as output_tmp_dir:
            for output_name, output_table_metas in output_tables_meta.items():
                if not isinstance(output_table_metas, list):
                    output_table_metas = [output_table_metas]
                for index, output_table_meta in enumerate(output_table_metas):
                    if not download_dir:
                        output_data_file_path = "{}/{}/{}.csv".format(output_tmp_dir, output_name, index)
                        output_data_meta_file_path = "{}/{}/{}.meta".format(output_tmp_dir, output_name, index)
                    else:
                        output_data_file_path = "{}/{}/{}.csv".format(download_dir, output_name, index)
                        output_data_meta_file_path = "{}/{}/{}.meta".format(download_dir, output_name, index)
                    output_data_file_list.append(output_data_file_path)
                    output_data_meta_file_list.append(output_data_meta_file_path)
                    os.makedirs(os.path.dirname(output_data_file_path), exist_ok=True)
                    with Session() as sess:
                        if not output_table_meta:
                            raise NoFoundTable()
                        table = sess.get_table(
                            name=output_table_meta.get_name(),
                            namespace=output_table_meta.get_namespace())
                        cls.write_data_to_file(output_data_file_path, output_data_meta_file_path, table, need_head)
            if download_dir:
                return
            # tar
            output_data_tarfile = "{}/{}".format(output_tmp_dir, tar_file_name)
            tar = tarfile.open(output_data_tarfile, mode='w:gz')
            for index in range(0, len(output_data_file_list)):
                tar.add(output_data_file_list[index], os.path.relpath(output_data_file_list[index], output_tmp_dir))
                tar.add(output_data_meta_file_list[index],
                        os.path.relpath(output_data_meta_file_list[index], output_tmp_dir))
            tar.close()
            return send_file(output_data_tarfile, download_name=tar_file_name, as_attachment=True, mimetype='application/gzip')

    @classmethod
    def write_data_to_file(cls, output_data_file_path, output_data_meta_file_path, table, need_head):
        with open(output_data_file_path, 'w') as fw:
            data_meta = table.meta.get_data_meta()
            header = cls.get_data_header(table.meta.get_id_delimiter(), data_meta)
            with open(output_data_meta_file_path, 'w') as f:
                json.dump({'header': header}, f, indent=4)
            if table:
                write_header = False
                for v in cls.collect_data(table=table):
                    # save meta
                    if not write_header and need_head and header and table.meta.get_have_head():
                        if isinstance(header, list):
                            header = table.meta.get_id_delimiter().join(header)
                            fw.write(f'{header}\n')
                        write_header = True
                    delimiter = table.meta.get_id_delimiter()
                    if isinstance(v, str):
                        fw.write('{}\n'.format(v))
                    elif isinstance(v, list):
                        fw.write('{}\n'.format(delimiter.join([str(_v) for _v in v])))
                    else:
                        raise ValueError(f"type={type(v)}, v={v}")

    @staticmethod
    def collect_data(table):
        if table.data_type == DataType.DATAFRAME:
            for _, data in table.collect():
                for v in data:
                    yield v
        elif table.data_type == DataType.TABLE:
            for _k, _v in table.collect():
                yield table.meta.get_id_delimiter().join([_k, _v])
        else:
            return []

    @staticmethod
    def display_data(table_metas):
        datas = {}
        for key, metas in table_metas.items():
            datas[key] = []
            for meta in metas:
                if meta.data_type in [DataType.DATAFRAME, DataType.TABLE]:
                    datas[key].append({"data": meta.get_part_of_data(), "metadata": meta.get_data_meta()})
                else:
                    continue
        return datas

    @classmethod
    def query_output_data_table(cls, **kwargs):
        data_list = OutputDataTracking.query(**kwargs)
        outputs = {}
        for data in data_list:
            if data.f_output_key not in outputs:
                outputs[data.f_output_key] = []
            outputs[data.f_output_key].append({"namespace": data.f_namespace, "name": data.f_name})
        return outputs

    @classmethod
    def download_output_data(cls, tar_file_name, **kwargs):
        outputs = {}
        for key, tables in cls.query_output_data_table(**kwargs).items():
            if key not in outputs:
                outputs[key] = []
            for table in tables:
                outputs[key].append(storage.StorageTableMeta(
                    name=table.get("name"),
                    namespace=table.get("namespace")
                ))

        if not outputs:
            raise NoFoundTable()

        return cls.send_table(outputs, tar_file_name=tar_file_name)

    @classmethod
    def display_output_data(cls, **kwargs):
        outputs = {}
        for key, tables in cls.query_output_data_table(**kwargs).items():
            if key not in outputs:
                outputs[key] = []
            for table in tables:
                outputs[key].append(storage.StorageTableMeta(
                    name=table.get("name"),
                    namespace=table.get("namespace")
                ))
        return cls.display_data(outputs)

    @staticmethod
    def delete_data(namespace, name):
        with Session() as sess:
            table = sess.get_table(name=name, namespace=namespace)
            if table:
                table.destroy()
                return True
            return False

    @staticmethod
    def create_data_table(
            namespace, name, uri, partitions, data_meta, data_type, part_of_data=None, count=None, source=None
    ):
        engine, address = DataManager.uri_to_address(uri)
        storage_meta = storage.StorageTableBase(
            namespace=namespace, name=name, address=address,
            partitions=partitions, engine=engine,
            options=None,
            key_serdes_type=0,
            value_serdes_type=0,
            partitioner_type=0,
        )
        storage_meta.create_meta(
            data_meta=data_meta, part_of_data=part_of_data, count=count, source=source, data_type=data_type
        )

    @staticmethod
    def uri_to_address(uri):
        uri_schema = URI.from_string(uri).to_schema()
        engine = uri_schema.schema()
        if engine == StorageEngine.EGGROLL:
            address = EggRollAddress(namespace=uri_schema.namespace, name=uri_schema.name)
        elif uri_schema.schema() == StorageEngine.STANDALONE:
            address = StandaloneAddress(namespace=uri_schema.namespace, name=uri_schema.name)
        elif uri_schema.schema() == StorageEngine.HDFS:
            address = HDFSAddress(path=uri_schema.path, name_node=uri_schema.authority)
        elif uri_schema.schema() in [StorageEngine.PATH, StorageEngine.FILE]:
            address = PathAddress(path=uri_schema.path)
        elif uri_schema.schema() in [StorageEngine.HTTP]:
            address = ApiAddress(url=uri_schema.path)
        else:
            raise ValueError(f"uri {uri} engine could not be converted to an address")
        return engine, address

    @staticmethod
    def get_data_info(namespace, name):
        data_table_meta = storage.StorageTableMeta(name=name, namespace=namespace)
        if data_table_meta:
            data = {
                "namespace": namespace,
                "name": name,
                "count": data_table_meta.count,
                "meta": data_table_meta.get_data_meta(),
                "engine": data_table_meta.engine,
                "path": data_table_meta.address.engine_path,
                "source": data_table_meta.source,
                "data_type": data_table_meta.data_type
            }
            display_data = data_table_meta.part_of_data
            return data, display_data
        raise NoFoundTable(name=name, namespace=namespace)

    @staticmethod
    def get_data_header(delimiter, data_meta):
        header = []
        if data_meta.get("header"):
            header = data_meta.get("header")
            if isinstance(header, str):
                header = header.split(delimiter)
        else:
            for field in data_meta.get("schema_meta", {}).get("fields", []):
                header.append(field.get("name"))
        return header

    @staticmethod
    def deserialize_data(m):
        fields = m.partition(DELIMITER)
        return fields[0], pickle.loads(bytes.fromhex(fields[2]))

    @staticmethod
    def serialize_data(k, v):
        return f"{k}{DELIMITER}{pickle.dumps(v).hex()}"


class DatasetManager:
    @staticmethod
    def task_output_name(task_id, task_version):
        return f"output_data_{task_id}_{task_version}", uuid.uuid1().hex

    @staticmethod
    def get_output_name(uri):
        namespace, name = uri.split("/")[-2], uri.split("/")[-1]
        return namespace, name

    @classmethod
    def upload_data_path(cls, name, namespace, prefix=None, storage_engine=StorageEngine.HDFS):
        if storage_engine == StorageEngine.HDFS:
            return cls.default_hdfs_path(data_type="input", name=name, namespace=namespace, prefix=prefix)
        elif storage_engine == StorageEngine.FILE:
            return cls.default_localfs_path(data_type="input", name=name, namespace=namespace)

    @classmethod
    def output_data_uri(cls, storage_engine, task_id, is_multi=False):
        if storage_engine == StorageEngine.STANDALONE:
            uri = f"{storage_engine}://{STANDALONE_DATA_HOME}/{task_id}/{uuid.uuid1().hex}"
        elif storage_engine == StorageEngine.HDFS:
            uri = cls.default_output_fs_path(uuid.uuid1().hex, task_id, storage_engine=storage_engine)
        elif storage_engine == StorageEngine.FILE:
            uri = f"file://{cls.default_output_fs_path(uuid.uuid1().hex, task_id, storage_engine=storage_engine)}"
        else:
            # egg: eggroll
            uri = f"{storage_engine}:///{task_id}/{uuid.uuid1().hex}"

        if is_multi:
            # replace "{index}"
            uri += "_{index}"
        return uri

    @classmethod
    def output_local_uri(cls, name, type_name, task_info, is_multi=False):
        path = job_utils.get_task_directory(**task_info, output=True)
        uri = os.path.join(f"file://{path}", name, type_name)
        if is_multi:
            # replace "{index}"
            uri += "_{index}"
        return uri

    @classmethod
    def default_output_fs_path(cls, name, namespace, prefix=None, storage_engine=StorageEngine.HDFS):
        if storage_engine == StorageEngine.HDFS:
            return f'{STORAGE.get(storage_engine).get("name_node")}' \
                   f'{cls.default_hdfs_path(data_type="output", name=name, namespace=namespace, prefix=prefix)}'
        elif storage_engine == StorageEngine.FILE:
            return cls.default_localfs_path(data_type="output", name=name, namespace=namespace)

    @staticmethod
    def default_localfs_path(name, namespace, data_type):
        return os.path.join(LOCALFS_DATA_HOME, namespace, name)

    @staticmethod
    def default_hdfs_path(data_type, name, namespace, prefix=None):
        p = f"/fate/{data_type}/{namespace}/{name}"
        if prefix:
            p = f"{prefix}/{p}"
        return p
