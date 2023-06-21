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
import tarfile
from tempfile import TemporaryDirectory

from flask import send_file

from fate_flow.engine import storage
from fate_flow.engine.storage import Session, StorageEngine
from fate_flow.entity.types import EggRollAddress, StandaloneAddress, HDFSAddress, PathAddress
from fate_flow.utils.io_utils import URI


class DataManager:
    @staticmethod
    def send_table(
            output_tables_meta,
            tar_file_name="",
            limit=-1,
            need_head=True,
            download_dir="",

    ):
        output_data_file_list = []
        output_data_meta_file_list = []
        with TemporaryDirectory() as output_tmp_dir:
            for output_name, output_table_meta in output_tables_meta.items():
                output_data_count = 0
                if not download_dir:
                    output_data_file_path = "{}/{}.csv".format(output_tmp_dir, output_name)
                    output_data_meta_file_path = "{}/{}.meta".format(output_tmp_dir, output_name)
                else:
                    output_data_file_path = "{}/{}.csv".format(download_dir, output_name)
                    output_data_meta_file_path = "{}/{}.meta".format(download_dir, output_name)
                os.makedirs(os.path.dirname(output_data_file_path), exist_ok=True)
                with open(output_data_file_path, 'w') as fw:
                    with Session() as sess:
                        output_table = sess.get_table(name=output_table_meta.get_name(),
                                                      namespace=output_table_meta.get_namespace())
                        if output_table:
                            for k, v in output_table.collect():
                                # save meta
                                if output_data_count == 0:
                                    output_data_file_list.append(output_data_file_path)
                                    schema = output_table.meta.get_data_meta()
                                    header = schema.get("header", [])
                                    output_data_meta_file_list.append(output_data_meta_file_path)
                                    with open(output_data_meta_file_path, 'w') as f:
                                        json.dump({'header': header}, f, indent=4)
                                    if need_head and header and output_table_meta.get_have_head():
                                        if isinstance(header, list):
                                            header = output_table_meta.get_id_delimiter().join(header)
                                        fw.write(f'{header}\n')
                                delimiter = output_table_meta.get_id_delimiter() if output_table_meta.get_id_delimiter() else ","
                                fw.write('{}\n'.format(delimiter.join([k, v])))
                                output_data_count += 1
                                if output_data_count == limit:
                                    break
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
            return send_file(output_data_tarfile, download_name=tar_file_name, as_attachment=True)

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
            namespace, name, uri, partitions, data_meta, origin, part_of_data=None, count=None
    ):
        engine, address = DataManager.uri_to_address(uri)
        storage_meta = storage.StorageTableBase(
            namespace=namespace, name=name, address=address,
            partitions=partitions, engine=engine,
            options=None
        )
        storage_meta.create_meta(
            data_meta=data_meta, part_of_data=part_of_data, count=count, origin=origin,
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
            address = HDFSAddress(path=uri_schema.path)
        elif uri_schema.schema() in [StorageEngine.PATH, StorageEngine.FILE]:
            address = PathAddress(path=uri_schema.path)
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
                "path": data_table_meta.address.engine_path
            }
            display_data = data_table_meta.part_of_data
            return data, display_data
        return {}
