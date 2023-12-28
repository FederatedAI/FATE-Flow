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
# GRPC
GRPC_SERVER_MAX_WORKERS = None  # default: (os.cpu_count() or 1) * 5

# Request
HTTP_REQUEST_TIMEOUT = 10  # s
REMOTE_REQUEST_TIMEOUT = 30000  # ms

LOG_DIR = ""
DATA_DIR = ""
MODEL_DIR = ""
JOB_DIR = ""
DEFAULT_FATE_DIR = ""

# sqlite
SQLITE_FILE_DIR = ""
SQLITE_FILE_NAME = "fate_flow_sqlite.db"


# Client Manager
APP_TOKEN_LENGTH = 16
ADMIN_ID = "admin"
ADMIN_KEY = "fate_flow_admin"
