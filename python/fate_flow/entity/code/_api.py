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
class ReturnCode:

    class Base:
        SUCCESS = 0

    class Job:
        NOT_FOUND = 1000
        CREATE_JOB_FAILED = 1001
        UPDATE_FAILED = 1002
        KILL_FAILED = 1003
        RESOURCE_EXCEPTION = 1004
        INHERITANCE_FAILED = 1005

    class Task:
        NOT_FOUND = 2000
        START_FAILED = 2001
        UPDATE_FAILED = 2002
        KILL_FAILED = 2003
        RESOURCE_EXCEPTION = 2004
        NO_FOUND_MODEL_OUTPUT = 2005

    class Site:
        IS_STANDALONE = 3000

    class Provider:
        PARAMS_ERROR = 4000
        DEVICE_NOT_SUPPORTED = 4001

    class API:
        EXPIRED = 5000
        INVALID_PARAMETER = 5001
        NO_FOUND_APPID = 5002
        VERIFY_FAILED = 5003
        AUTHENTICATION_FAILED = 5004

    class Server:
        EXCEPTION = 6000
        FUNCTION_RESTRICTED = 6001
        RESPONSE_EXCEPTION = 6002
        NO_FOUND = 6003
        NO_FOUND_INSTANCE = 6004

    class Table:
        NO_FOUND = 7001

    class File:
        FILE_NOT_FOUND = 8001
        FILE_EXISTS = 8002