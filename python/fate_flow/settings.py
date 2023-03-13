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
import os

from fate_flow.utils.file_utils import get_fate_flow_directory
from fate_flow.utils.log import LoggerFactory

# GRPC
GRPC_SERVER_MAX_WORKERS = None

# Request
HTTP_REQUEST_TIMEOUT = 10  # s
REMOTE_REQUEST_TIMEOUT = 30000  # ms

# Logger
LOG_DIRECTORY = get_fate_flow_directory("logs")
LoggerFactory.set_directory(os.path.join(LOG_DIRECTORY, "fate_flow"))
# {CRITICAL: 50, FATAL:50, ERROR:40, WARNING:30, WARN:30, INFO:20, DEBUG:10, NOTSET:0}
LoggerFactory.LEVEL = 10

# Client Manager
APP_TOKEN_LENGTH = 16
ADMIN_ID = "admin"
ADMIN_KEY = "fate_flow_admin"
