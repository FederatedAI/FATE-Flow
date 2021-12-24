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
import traceback

import pymysql

from fate_arch.common import log
from fate_arch.storage import StorageTableBase
from fate_flow.component_env_utils import feature_utils
from fate_flow.external.storage.base import Storage, MysqlAddress
from fate_flow.manager.data_manager import get_component_output_data_schema

LOGGER = log.getLogger()


class MysqlStorage(Storage):
    def __init__(self, address: dict, storage_table: StorageTableBase):
        self.address = MysqlAddress(**address)
        self.storage_table = storage_table
        self._con = None
        self._cur = None
        self._connect()

    def save(self):
        create = False
        sql = None
        max = 10000
        count = 0
        LOGGER.info(f"start save Table({self.storage_table.namespace}, {self.storage_table.name}) to Mysql({self.address.db}, {self.address.name})")
        join_delimiter = ","
        for k, v in self.storage_table.collect():
            v, extend_header = feature_utils.get_deserialize_value(v, join_delimiter)
            if not create:
                _, header_list = self._create_table(extend_header)
                LOGGER.info("craete table success")
                create = True
            if not sql:
                sql = "REPLACE INTO {}({}, {})  VALUES".format(
                    self.address.name, header_list[0], ",".join(header_list[1:])
                )
            sql += '("{}", "{}"),'.format(k, '", "'.join(v.split(join_delimiter)))
            count += 1
            if not count % max:
                sql = ",".join(sql.split(",")[:-1]) + ";"
                self._cur.execute(sql)
                self._con.commit()
                sql = None
                LOGGER.info(f"save data count:{count}")
        if count > 0:
            sql = ",".join(sql.split(",")[:-1]) + ";"
            self._cur.execute(sql)
            self._con.commit()
            LOGGER.info(f"save success, count:{count}")

    def _create_table(self, extend_header):
        header_list = get_component_output_data_schema(self.storage_table.meta, extend_header)
        feature_sql = self.get_create_features_sql(header_list[1:])
        id_size = "varchar(100)"
        create_table = (
            "create table if not exists {}({} {} NOT NULL, {} PRIMARY KEY({}))".format(
                self.address.name, header_list[0], id_size, feature_sql, header_list[0]
            )
        )
        LOGGER.info(f"create table {self.address.name}: {create_table}")
        return self._cur.execute(create_table), header_list

    @staticmethod
    def get_create_features_sql(feature_name_list):
        create_features = ""
        feature_list = []
        feature_size = "varchar(255)"
        for feature_name in feature_name_list:
            create_features += "{} {},".format(feature_name, feature_size)
            feature_list.append(feature_name)
        return create_features

    def _create_db_if_not_exists(self):
        connection = pymysql.connect(host=self.address.host,
                                     user=self.address.user,
                                     password=self.address.passwd,
                                     port=self.address.port)
        with connection:
            with connection.cursor() as cursor:
                cursor.execute("create database if not exists {}".format(self.address.db))
                print('create db {} success'.format(self.address.db))
            connection.commit()

    def _connect(self):
        LOGGER.info(f"start connect database {self.address.db}")
        self._con = pymysql.connect(host=self.address.host,
                                    user=self.address.user,
                                    passwd=self.address.passwd,
                                    port=self.address.port,
                                    db=self.address.db)
        self._cur = self._con.cursor()
        LOGGER.info(f"connect success!")

    def _open(self):
        return self

    def __enter__(self):
        self._connect()
        return self._open()

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            LOGGER.info("close connect")
            self._cur.close()
            self._con.close()
        except Exception as e:
            traceback.print_exc()