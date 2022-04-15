#!/usr/bin/env python
# -*- coding: utf-8 -*-
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
import numpy as np
from fate_arch import session
from fate_arch.abc import AddressABC, StorageTableABC, StorageTableMetaABC
from fate_arch.common import EngineType, log
from fate_arch.common.data_utils import default_output_fs_path, default_output_info
from fate_arch.computing import ComputingEngine
from fate_arch.session import Session
from fate_arch.storage import StorageEngine, StorageTableMeta, StorageTableOrigin
from fate_flow.components._base import (
    BaseParam,
    ComponentBase,
    ComponentInputProtocol,
    ComponentMeta,
)
from fate_flow.errors import ParameterError
from fate_flow.entity import MetricMeta
from fate_flow.entity.types import InputSearchType
from fate_flow.manager.data_manager import DataTableTracker, TableStorage
from fate_flow.operation.job_tracker import Tracker
from fate_flow.utils import data_utils

LOGGER = log.getLogger()
MAX_NUM = 10000

reader_cpn_meta = ComponentMeta("Reader")


@reader_cpn_meta.bind_param
class ReaderParam(BaseParam):
    def __init__(self, table=None):
        self.table = table

    def check(self):
        return True


@reader_cpn_meta.bind_runner.on_guest.on_host
class Reader(ComponentBase):
    def __init__(self):
        super(Reader, self).__init__()
        self.parameters = None
        self.job_parameters = None

    def _run(self, cpn_input: ComponentInputProtocol):
        self.parameters = cpn_input.parameters
        self.job_parameters = cpn_input.job_parameters
        output_storage_address = self.job_parameters.engines_address[EngineType.STORAGE]
        # only support one input table
        table_key = [key for key in self.parameters.keys()][0]

        input_table_namespace, input_table_name = self.get_input_table_info(
            parameters=self.parameters[table_key],
            role=self.tracker.role,
            party_id=self.tracker.party_id,
        )
        (
            output_table_namespace,
            output_table_name,
        ) = default_output_info(
            task_id=self.tracker.task_id, 
            task_version=self.tracker.task_version,
            output_type="data",
        )
        (
            input_table_meta,
            output_table_address,
            output_table_engine,
        ) = self.convert_check(
            input_name=input_table_name,
            input_namespace=input_table_namespace,
            output_name=output_table_name,
            output_namespace=output_table_namespace,
            computing_engine=self.job_parameters.computing_engine,
            output_storage_address=output_storage_address,
        )
        sess = Session.get_global()

        input_table = sess.get_table(
            name=input_table_meta.get_name(), namespace=input_table_meta.get_namespace()
        )
        # update real count to meta info
        input_table.count()
        # Table replication is required
        if input_table_meta.get_engine() != output_table_engine:
            LOGGER.info(
                f"the {input_table_meta.get_engine()} engine input table needs to be converted to {output_table_engine} engine to support computing engine {self.job_parameters.computing_engine}"
            )
        else:
            LOGGER.info(
                f"the {input_table_meta.get_engine()} input table needs to be transform format"
            )
        LOGGER.info("reader create storage session2")
        output_table_session = sess.storage(storage_engine=output_table_engine)
        output_table = output_table_session.create_table(
            address=output_table_address,
            name=output_table_name,
            namespace=output_table_namespace,
            partitions=input_table_meta.partitions,
            origin=StorageTableOrigin.READER
        )
        self.save_table(src_table=input_table, dest_table=output_table)
        # update real count to meta info
        output_table_meta = StorageTableMeta(
            name=output_table.name, namespace=output_table.namespace
        )
        # todo: may be set output data, and executor support pass persistent
        self.tracker.log_output_data_info(
            data_name=cpn_input.flow_feeded_parameters.get("output_data_name")[0]
            if cpn_input.flow_feeded_parameters.get("output_data_name")
            else table_key,
            table_namespace=output_table_meta.get_namespace(),
            table_name=output_table_meta.get_name(),
        )
        DataTableTracker.create_table_tracker(
            output_table_meta.get_name(),
            output_table_meta.get_namespace(),
            entity_info={
                "have_parent": True,
                "parent_table_namespace": input_table_namespace,
                "parent_table_name": input_table_name,
                "job_id": self.tracker.job_id,
            },
        )
        headers_str = output_table_meta.get_schema().get("header")
        table_info = {}
        if output_table_meta.get_schema() and headers_str:
            if isinstance(headers_str, str):
                data_list = [headers_str.split(",")]
                is_display = True
            else:
                data_list = [headers_str]
                is_display = False
            if is_display:
                for data in output_table_meta.get_part_of_data():
                    data_list.append(data[1].split(","))
                data = np.array(data_list)
                Tdata = data.transpose()
                for data in Tdata:
                    table_info[data[0]] = ",".join(list(set(data[1:]))[:5])
        data_info = {
            "table_name": input_table_name,
            "namespace": input_table_namespace,
            "table_info": table_info,
            "partitions": output_table_meta.get_partitions(),
            "storage_engine": output_table_meta.get_engine(),
        }
        if input_table_meta.get_engine() in [StorageEngine.PATH]:
            data_info["file_count"] = output_table_meta.get_count()
            data_info["file_path"] = input_table_meta.get_address().path
        else:
            data_info["count"] = output_table_meta.get_count()

        self.tracker.set_metric_meta(
            metric_namespace="reader_namespace",
            metric_name="reader_name",
            metric_meta=MetricMeta(
                name="reader", metric_type="data_info", extra_metas=data_info
            ),
        )

    @staticmethod
    def get_input_table_info(parameters, role, party_id):
        search_type = data_utils.get_input_search_type(parameters)
        if search_type is InputSearchType.TABLE_INFO:
            return parameters["namespace"], parameters["name"]
        elif search_type is InputSearchType.JOB_COMPONENT_OUTPUT:
            output_data_infos = Tracker.query_output_data_infos(
                job_id=parameters["job_id"],
                component_name=parameters["component_name"],
                data_name=parameters["data_name"],
                role=role,
                party_id=party_id,
            )
            if not output_data_infos:
                raise Exception(f"can not found input table, please check parameters")
            else:
                namespace, name = (
                    output_data_infos[0].f_table_namespace,
                    output_data_infos[0].f_table_name,
                )
                LOGGER.info(f"found input table {namespace} {name} by {parameters}")
                return namespace, name
        else:
            raise ParameterError(
                f"can not found input table info by parameters {parameters}"
            )

    @staticmethod
    def convert_check(
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

    def deal_linkis_hive(self, src_table: StorageTableABC, dest_table: StorageTableABC):
        import functools

        from pyspark.sql import SparkSession

        session = SparkSession.builder.enableHiveSupport().getOrCreate()
        src_data = session.sql(
            f"select * from {src_table.address.database}.{src_table.address.name}"
        )
        LOGGER.info(
            f"database:{src_table.address.database}, name:{src_table.address.name}"
        )
        LOGGER.info(f"src data: {src_data}")
        # src_data = src_table.collect(is_spark=1)
        src_data = src_data.toPandas().astype(str)
        LOGGER.info(f"columns: {src_data.columns}")
        header_source_item = list(src_data.columns)

        id_delimiter = src_table.meta.get_id_delimiter()
        LOGGER.info(f"id_delimiter: {id_delimiter}")
        LOGGER.info(f"src_data: {src_data}")
        src_data.applymap(lambda x: str(x))
        f = functools.partial(self.convert_join, delimitor=id_delimiter)
        src_data["result"] = src_data.agg(f, axis=1)
        dest_data = src_data.iloc[:, [0, -1]]
        dest_data.columns = ["key", "value"]
        LOGGER.info(f"dest_data: {dest_data}")
        LOGGER.info(
            f"database:{dest_table.address.database}, name:{dest_table.address.name}"
        )
        dest_table.put_all(dest_data)
        schema = {
            "header": id_delimiter.join(header_source_item[1:]).strip(),
            "sid": header_source_item[0].strip(),
        }
        dest_table.meta.update_metas(schema=schema)

    def convert_join(self, x, delimitor=","):
        import pickle

        x = [str(i) for i in x]
        return pickle.dumps(delimitor.join(x[1:])).hex()

    def save_table(self, src_table: StorageTableABC, dest_table: StorageTableABC):
        LOGGER.info(f"start copying table")
        LOGGER.info(
            f"source table name: {src_table.name} namespace: {src_table.namespace} engine: {src_table.engine}"
        )
        LOGGER.info(
            f"destination table name: {dest_table.name} namespace: {dest_table.namespace} engine: {dest_table.engine}"
        )
        if src_table.engine == dest_table.engine and src_table.meta.get_in_serialized():
            self.to_save(src_table, dest_table)
        else:
            TableStorage.copy_table(src_table, dest_table)

    def to_save(self, src_table, dest_table):
        src_table_meta = src_table.meta
        src_computing_table = session.get_computing_session().load(
            src_table_meta.get_address(),
            schema=src_table_meta.get_schema(),
            partitions=src_table_meta.get_partitions(),
            id_delimiter=src_table_meta.get_id_delimiter(),
            in_serialized=src_table_meta.get_in_serialized(),
        )
        LOGGER.info(f"schema: {src_table_meta.get_schema()}")
        schema = src_table_meta.get_schema()
        self.tracker.job_tracker.save_output_data(
            src_computing_table,
            output_storage_engine=dest_table.engine,
            output_storage_address=dest_table.address.__dict__,
            output_table_namespace=dest_table.namespace,
            output_table_name=dest_table.name,
            schema=schema,
            need_read=False
        )
        dest_table.meta.update_metas(schema=schema, part_of_data=src_table_meta.get_part_of_data(), count=src_table_meta.get_count())
        LOGGER.info(
            f"save {dest_table.namespace} {dest_table.name} success"
        )
