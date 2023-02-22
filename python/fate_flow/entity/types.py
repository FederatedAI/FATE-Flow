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


class ProcessRole(CustomEnum):
    DRIVER = "driver"
    WORKER = "worker"


class ResourceOperation(CustomEnum):
    APPLY = "apply"
    RETURN = "return"


class CoordinationCommunicationProtocol(object):
    HTTP = "http"
    GRPC = "grpc"


class FederatedMode(object):
    SINGLE = "SINGLE"
    MULTIPLE = "MULTIPLE"

    def is_single(self, value):
        return value == self.SINGLE

    def is_multiple(self, value):
        return value == self.MULTIPLE


class KillProcessRetCode(IntEnum, CustomEnum):
    KILLED = 0
    NOT_FOUND = 1
    ERROR_PID = 2


class WorkerName(CustomEnum):
    TASK_EXECUTOR = "task_executor"
    TASK_INITIALIZER = "task_initializer"
    PROVIDER_REGISTRAR = "provider_registrar"
    DEPENDENCE_UPLOAD = "dependence_upload"


class ArtifactSourceType(object):
    TASK_OUTPUT_ARTIFACT = "task_output_artifact"
    MODEL_WAREHOUSE = "model_warehouse"


class Stage(object):
    TRAIN = "train"
    PREDICT = "predict"
    DEFAULT = "default"


class ReturnCode:

    class Base:
        SUCCESS = 0
        EXCEPTION_ERROR = 100

    class Job:
        NOT_FOUND = 1000
        CREATE_JOB_FAILED = 1001
        UPDATE_STATUS_FAILED = 1002
        UPDATE_FAILED = 1003
        KILL_FAILED = 1004
        APPLY_RESOURCE_FAILED = 1005

    class Task:
        NOT_FOUND = 2000
        START_FAILED = 2001
        UPDATE_STATUS_FAILED = 2002
        UPDATE_FAILED = 2003
        KILL_FAILED = 2004
        APPLY_RESOURCE_FAILED = 2005

    class Site:
        IS_STANDALONE = 3000
