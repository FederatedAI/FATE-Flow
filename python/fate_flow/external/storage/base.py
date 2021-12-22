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
import abc


class AddressABC(metaclass=abc.ABCMeta):
    ...


class Storage(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def save(self):
        ...


class MysqlAddress(AddressABC):
    def __init__(self, user, passwd, host, port, db, name, **kwargs):
        self.user = user
        self.passwd = passwd
        self.host = host
        self.port = port
        self.db = db
        self.name = name

    def __hash__(self):
        return (self.host, self.port, self.db, self.name).__hash__()

    def __str__(self):
        return f"MysqlAddress(db={self.db}, name={self.name})"

    def __repr__(self):
        return self.__str__()
