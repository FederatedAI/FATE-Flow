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
from fate_arch.abc import StorageTableMetaABC, AddressABC
from fate_arch.common.data_utils import default_output_fs_path
from fate_arch.computing import ComputingEngine
from fate_arch.storage import StorageEngine, StorageTableMeta
from fate_flow.entity.types import InputSearchType
from fate_arch import storage


def get_header_schema(header_line, id_delimiter, extend_sid=False):
    header_source_item = header_line.split(id_delimiter)
    if extend_sid:
        header = id_delimiter.join(header_source_item).strip()
        sid = get_extend_id_name()
    else:
        header = id_delimiter.join(header_source_item[1:]).strip()
        sid = header_source_item[0].strip()
    return {'header': header, 'sid': sid}


def get_extend_id_name():
    return "extend_sid"


def get_sid_data_line(values, id_delimiter, fate_uuid, line_index, **kwargs):
    return line_extend_uuid(fate_uuid, line_index), list_to_str(values, id_delimiter=id_delimiter)


def line_extend_uuid(fate_uuid, line_index):
    return fate_uuid + str(line_index)


def get_auto_increasing_sid_data_line(values, id_delimiter, line_index, **kwargs):
    return line_index, list_to_str(values, id_delimiter=id_delimiter)


def get_data_line(values, id_delimiter, **kwargs):
    return values[0], list_to_str(values[1:], id_delimiter=id_delimiter)


def list_to_str(input_list, id_delimiter):
    return id_delimiter.join(list(map(str, input_list)))


def convert_output(
        input_name,
        input_namespace,
        output_name,
        output_namespace,
        computing_engine: ComputingEngine = ComputingEngine.EGGROLL,
        output_storage_address={},
    ) -> (StorageTableMetaABC, AddressABC, StorageEngine):
        input_table_meta = StorageTableMeta(name=input_name, namespace=input_namespace)

        if not input_table_meta:
            raise RuntimeError(
                f"can not found table name: {input_name} namespace: {input_namespace}"
            )
        address_dict = output_storage_address.copy()
        if input_table_meta.get_engine() in [StorageEngine.PATH]:
            from fate_arch.storage import PathStoreType

            address_dict["name"] = output_name
            address_dict["namespace"] = output_namespace
            address_dict["storage_type"] = PathStoreType.PICTURE
            address_dict["path"] = input_table_meta.get_address().path
            output_table_address = StorageTableMeta.create_address(
                storage_engine=StorageEngine.PATH, address_dict=address_dict
            )
            output_table_engine = StorageEngine.PATH
        elif computing_engine == ComputingEngine.STANDALONE:
            from fate_arch.storage import StandaloneStoreType

            address_dict["name"] = output_name
            address_dict["namespace"] = output_namespace
            address_dict["storage_type"] = StandaloneStoreType.ROLLPAIR_LMDB
            output_table_address = StorageTableMeta.create_address(
                storage_engine=StorageEngine.STANDALONE, address_dict=address_dict
            )
            output_table_engine = StorageEngine.STANDALONE
        elif computing_engine == ComputingEngine.EGGROLL:
            from fate_arch.storage import EggRollStoreType

            address_dict["name"] = output_name
            address_dict["namespace"] = output_namespace
            address_dict["storage_type"] = EggRollStoreType.ROLLPAIR_LMDB
            output_table_address = StorageTableMeta.create_address(
                storage_engine=StorageEngine.EGGROLL, address_dict=address_dict
            )
            output_table_engine = StorageEngine.EGGROLL
        elif computing_engine == ComputingEngine.SPARK:
            if input_table_meta.get_engine() == StorageEngine.HIVE:
                output_table_address = input_table_meta.get_address()
                output_table_address.name = output_name
                output_table_engine = input_table_meta.get_engine()
            elif input_table_meta.get_engine() == StorageEngine.LOCALFS:
                output_table_address = input_table_meta.get_address()
                output_table_address.path = default_output_fs_path(
                    name=output_name,
                    namespace=output_namespace,
                    storage_engine=StorageEngine.LOCALFS
                )
                output_table_engine = input_table_meta.get_engine()
            else:
                address_dict["path"] = default_output_fs_path(
                    name=output_name,
                    namespace=output_namespace,
                    prefix=address_dict.get("path_prefix"),
                    storage_engine=StorageEngine.HDFS
                )
                output_table_address = StorageTableMeta.create_address(
                    storage_engine=StorageEngine.HDFS, address_dict=address_dict
                )
                output_table_engine = StorageEngine.HDFS
        elif computing_engine == ComputingEngine.LINKIS_SPARK:
            output_table_address = input_table_meta.get_address()
            output_table_address.name = output_name
            output_table_engine = input_table_meta.get_engine()
        else:
            raise RuntimeError(f"can not support computing engine {computing_engine}")
        return input_table_meta, output_table_address, output_table_engine


def get_input_data_min_partitions(input_data, role, party_id):
    min_partition = None
    if role != 'arbiter':
        for data_type, data_location in input_data[role][party_id].items():
            table_info = {'name': data_location.split('.')[1], 'namespace': data_location.split('.')[0]}
            table_meta = storage.StorageTableMeta(name=table_info['name'], namespace=table_info['namespace'])
            if table_meta:
                table_partition = table_meta.get_partitions()
                if not min_partition or min_partition > table_partition:
                    min_partition = table_partition
    return min_partition


def get_input_search_type(parameters):
    if "name" in parameters and "namespace" in parameters:
        return InputSearchType.TABLE_INFO
    elif "job_id" in parameters and "component_name" in parameters and "data_name" in parameters:
        return InputSearchType.JOB_COMPONENT_OUTPUT
    else:
        return InputSearchType.UNKNOWN
