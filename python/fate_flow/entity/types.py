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
from enum import IntEnum
from ._base import BaseEntity
import typing
from fate_arch.common import DTable


class BaseType(object):
    #todo: may be use enum?
    @classmethod
    def types(cls):
        return [cls.__dict__[k] for k in cls.__dict__.keys() if not callable(getattr(cls, k)) and not k.startswith("__")]

    @classmethod
    def contains(cls, status):
        return status in cls.types()


class ComponentProviderName(BaseType):
    FATE_ALGORITHM = "fate_algorithm"
    AVATAR_ALGORITHM = "avatar_algorithm"
    FATE_FLOW_TOOLS = "fate_flow_tools"


class ModelStorage(object):
    REDIS = "redis"
    MYSQL = "mysql"


class ModelOperation(object):
    STORE = "store"
    RESTORE = "restore"
    EXPORT = "export"
    IMPORT = "import"
    LOAD = "load"
    BIND = "bind"


class ProcessRole(object):
    DRIVER = "driver"
    WORKER = "worker"


class TagOperation(object):
    CREATE = "create"
    RETRIEVE = "retrieve"
    UPDATE = "update"
    DESTROY = "destroy"
    LIST = "list"


class ResourceOperation(object):
    APPLY = "apply"
    RETURN = "return"


class KillProcessRetCode(object):
    KILLED = 0
    NOT_FOUND = 1
    ERROR_PID = 2


class InputSearchType(IntEnum):
    UNKNOWN = 0
    TABLE_INFO = 1
    JOB_COMPONENT_OUTPUT = 2


class DataCache(BaseEntity):
    def __init__(self, name: str, key: str = None, data: typing.Dict[str, DTable] = None, meta: dict = None, job_id: str = None, component_name: str = None, task_id: str = None, task_version: int = None):
        self._name: str = name
        self._key: str = key
        self._data: typing.Dict[str, DTable] = data if data else {}
        self._meta: dict = meta
        self._job_id = job_id
        self._component_name = component_name
        self._task_id: str = task_id
        self._task_version: int = task_version

    @property
    def name(self):
        return self._name

    @property
    def key(self):
        return self._key

    @key.setter
    def key(self, key: str):
        self._key = key

    @property
    def data(self):
        return self._data

    @property
    def meta(self):
        return self._meta

    @property
    def job_id(self):
        return self._job_id

    @job_id.setter
    def job_id(self, job_id: str):
        self._job_id = job_id

    @property
    def component_name(self):
        return self._component_name

    @component_name.setter
    def component_name(self, component_name: str):
        self._component_name = component_name

    @property
    def task_id(self):
        return self._task_id

    @task_id.setter
    def task_id(self, task_id: str):
        self._task_id = task_id

    @property
    def task_version(self):
        return self._task_version

    @task_version.setter
    def task_version(self, task_version: int):
        self._task_version = task_version


class WorkerName:
    TASK_EXECUTOR = "task_executor"
    TASK_INITIALIZER = "task_initializer"
    PROVIDER_REGISTRAR = "provider_registrar"
