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
import abc


class AddressABC(metaclass=abc.ABCMeta):
    ...


class AddressBase(AddressABC):
    def __init__(self, connector_name=None):
        pass

    @property
    def connector(self):
        return {}

    @property
    def storage_engine(self):
        return

    @property
    def engine_path(self):
        return


class StandaloneAddress(AddressBase):
    def __init__(self, home=None, name=None, namespace=None, storage_type=None, connector_name=None):
        self.home = home
        self.name = name
        self.namespace = namespace
        self.storage_type = storage_type
        super(StandaloneAddress, self).__init__(connector_name=connector_name)

    def __hash__(self):
        return (self.home, self.name, self.namespace, self.storage_type).__hash__()

    def __str__(self):
        return f"StandaloneAddress(name={self.name}, namespace={self.namespace})"

    def __repr__(self):
        return self.__str__()

    @property
    def connector(self):
        return {"home": self.home}

    @property
    def engine_path(self):
        if self.home:
            return f"standalone:///{self.home}/{self.namespace}/{self.name}"
        else:
            return f"standalone:///{self.namespace}/{self.name}"


class EggRollAddress(AddressBase):
    def __init__(self, home=None, name=None, namespace=None, connector_name=None):
        self.name = name
        self.namespace = namespace
        self.home = home
        super(EggRollAddress, self).__init__(connector_name=connector_name)

    def __hash__(self):
        return (self.home, self.name, self.namespace).__hash__()

    def __str__(self):
        return f"EggRollAddress(name={self.name}, namespace={self.namespace})"

    def __repr__(self):
        return self.__str__()

    @property
    def connector(self):
        return {"home": self.home}

    @property
    def engine_path(self):
        return f"eggroll:///{self.namespace}/{self.name}"


class HDFSAddress(AddressBase):
    def __init__(self, name_node=None, path=None, connector_name=None):
        self.name_node = name_node
        self.path = path
        super(HDFSAddress, self).__init__(connector_name=connector_name)

    def __hash__(self):
        return (self.name_node, self.path).__hash__()

    def __str__(self):
        return f"HDFSAddress(name_node={self.name_node}, path={self.path})"

    def __repr__(self):
        return self.__str__()

    @property
    def engine_path(self):
        if not self.name_node:
            return f"hdfs://{self.path}"
        else:
            if "hdfs" not in self.name_node:
                return f"hdfs://{self.name_node}{self.path}"
            else:
                return f"{self.name_node}{self.path}"

    @property
    def connector(self):
        return {"name_node": self.name_node}


class PathAddress(AddressBase):
    def __init__(self, path=None, connector_name=None):
        self.path = path
        super(PathAddress, self).__init__(connector_name=connector_name)

    def __hash__(self):
        return self.path.__hash__()

    def __str__(self):
        return f"PathAddress(path={self.path})"

    def __repr__(self):
        return self.__str__()

    @property
    def engine_path(self):
        return f"file://{self.path}"


class ApiAddress(AddressBase):
    def __init__(self, method="POST", url=None, header=None, body=None, connector_name=None):
        self.method = method
        self.url = url
        self.header = header if header else {}
        self.body = body if body else {}
        super(ApiAddress, self).__init__(connector_name=connector_name)

    def __hash__(self):
        return (self.method, self.url).__hash__()

    def __str__(self):
        return f"ApiAddress(url={self.url})"

    def __repr__(self):
        return self.__str__()

    @property
    def engine_path(self):
        return self.url


class MysqlAddress(AddressBase):
    def __init__(self, user=None, passwd=None, host=None, port=None, db=None, name=None, connector_name=None):
        self.user = user
        self.passwd = passwd
        self.host = host
        self.port = port
        self.db = db
        self.name = name
        self.connector_name = connector_name
        super(MysqlAddress, self).__init__(connector_name=connector_name)

    def __hash__(self):
        return (self.host, self.port, self.db, self.name).__hash__()

    def __str__(self):
        return f"MysqlAddress(db={self.db}, name={self.name})"

    def __repr__(self):
        return self.__str__()

    @property
    def connector(self):
        return {"user": self.user, "passwd": self.passwd, "host": self.host, "port": self.port, "db": self.db}


class HiveAddress(AddressBase):
    def __init__(self, host=None, name=None, port=10000, username=None, database='default', auth_mechanism='PLAIN',
                 password=None, connector_name=None):
        self.host = host
        self.username = username
        self.port = port
        self.database = database
        self.auth_mechanism = auth_mechanism
        self.password = password
        self.name = name
        super(HiveAddress, self).__init__(connector_name=connector_name)

    def __hash__(self):
        return (self.host, self.port, self.database, self.name).__hash__()

    def __str__(self):
        return f"HiveAddress(database={self.database}, name={self.name})"

    def __repr__(self):
        return self.__str__()

    @property
    def connector(self):
        return {
            "host": self.host,
            "port": self.port,
            "username": self.username,
            "password": self.password,
            "auth_mechanism": self.auth_mechanism,
            "database": self.database}


class FileAddress(AddressBase):
    def __init__(self, path=None, connector_name=None):
        self.path = path
        super(FileAddress, self).__init__(connector_name=connector_name)

    def __hash__(self):
        return self.path.__hash__()

    def __str__(self):
        return f"FileAddress(path={self.path})"

    def __repr__(self):
        return self.__str__()

    @property
    def engine_path(self):
        return f"file://{self.path}"
