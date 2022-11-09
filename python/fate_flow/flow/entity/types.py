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


class ResourceOperation(CustomEnum):
    APPLY = "apply"
    RETURN = "return"


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
    PERMISSION_ERROR = 108
    AUTHENTICATION_ERROR = 109
    SERVER_ERROR = 500


class Job:
    def __init__(self, **kwargs):
        self.f_job_id = ""
        self.f_roles = {}
        for k, v in kwargs.items():
            if hasattr(self, k.strip("f_")):
                setattr(self, k, v)


class Task:
    def __init__(self, **kwargs):
        self.f_job_id = ""
        self.f_party_id = None
        self.f_role = ""
        self.f_component_name = ""
        self.f_task_id = ""
        self.f_task_version = 0
        for k, v in kwargs.items():
            if hasattr(self, k.strip("f_")):
                setattr(self, k, v)
