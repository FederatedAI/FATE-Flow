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
from enum import IntEnum, Enum


class CustomEnum(Enum):
    @classmethod
    def valid(cls, value):
        try:
            cls(value)
            return True
        except:
            return False

    @classmethod
    def values(cls):
        return [member.value for member in cls.__members__.values()]

    @classmethod
    def names(cls):
        return [member.name for member in cls.__members__.values()]


class ComponentProviderName(CustomEnum):
    FATE = "fate"
    FATE_FLOW = "fate_flow"
    FATE_SQL = "fate_sql"


class FateDependenceName(CustomEnum):
    Fate_Source_Code = "fate_code"
    Python_Env = "python_env"


class FateDependenceStorageEngine(CustomEnum):
    HDFS = "HDFS"


class PythonDependenceName(CustomEnum):
    Fate_Source_Code = "python"
    Python_Env = "miniconda"


class ModelStorage(CustomEnum):
    REDIS = "redis"
    MYSQL = "mysql"
    TENCENT_COS = "tencent_cos"


class ModelOperation(CustomEnum):
    STORE = "store"
    RESTORE = "restore"
    EXPORT = "export"
    IMPORT = "import"
    LOAD = "load"
    BIND = "bind"


class ProcessRole(CustomEnum):
    DRIVER = "driver"
    WORKER = "worker"


class TagOperation(CustomEnum):
    CREATE = "create"
    RETRIEVE = "retrieve"
    UPDATE = "update"
    DESTROY = "destroy"
    LIST = "list"


class ResourceOperation(CustomEnum):
    APPLY = "apply"
    RETURN = "return"


class KillProcessRetCode(IntEnum, CustomEnum):
    KILLED = 0
    NOT_FOUND = 1
    ERROR_PID = 2


class InputSearchType(IntEnum, CustomEnum):
    UNKNOWN = 0
    TABLE_INFO = 1
    JOB_COMPONENT_OUTPUT = 2


class RetCode(IntEnum, CustomEnum):
    SUCCESS = 0
    NOT_EFFECTIVE = 10
    EXCEPTION_ERROR = 100
    ARGUMENT_ERROR = 101
    DATA_ERROR = 102
    OPERATING_ERROR = 103
    FEDERATED_ERROR = 104
    CONNECTION_ERROR = 105
    RUNNING = 106
    INCOMPATIBLE_FATE_VER = 107
    SERVER_ERROR = 500


class WorkerName(CustomEnum):
    TASK_EXECUTOR = "task_executor"
    TASK_INITIALIZER = "task_initializer"
    PROVIDER_REGISTRAR = "provider_registrar"
    DEPENDENCE_UPLOAD = "dependence_upload"

class TaskCleanResourceType(CustomEnum):
    TABLE = "table"
    METRICS = "metrics"


class ExternalStorage(CustomEnum):
    MYSQL = "MYSQL"
