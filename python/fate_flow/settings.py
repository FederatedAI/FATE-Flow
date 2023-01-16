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

from fate_flow.entity.engine_types import ComputingEngine
from fate_flow.utils import engine_utils
from fate_flow.utils.conf_utils import get_base_config, decrypt_database_config
from fate_flow.utils.file_utils import get_fate_flow_directory
from fate_flow.utils.log_utils import LoggerFactory, getLogger

# Server
API_VERSION = "v2"
FATE_FLOW_SERVICE_NAME = "fateflow"
SERVER_MODULE = "fate_flow_server.py"
TEMP_DIRECTORY = os.path.join(get_fate_flow_directory(), "temp")
FATE_FLOW_CONF_PATH = os.path.join(get_fate_flow_directory(), "conf")

FATE_FLOW_JOB_DEFAULT_CONFIG_PATH = os.path.join(FATE_FLOW_CONF_PATH, "job_default_config.yaml")

SUBPROCESS_STD_LOG_NAME = "std.log"

GRPC_SERVER_MAX_WORKERS = None

HTTP_REQUEST_TIMEOUT = 10  # s

REMOTE_REQUEST_TIMEOUT = 30000  # ms

HOST = get_base_config(FATE_FLOW_SERVICE_NAME, {}).get("host", "127.0.0.1")
HTTP_PORT = get_base_config(FATE_FLOW_SERVICE_NAME, {}).get("http_port")
GRPC_PORT = get_base_config(FATE_FLOW_SERVICE_NAME, {}).get("grpc_port")

PROTOCOL = get_base_config(FATE_FLOW_SERVICE_NAME, {}).get("protocol", "http")

PROXY_NAME = get_base_config(FATE_FLOW_SERVICE_NAME, {}).get("proxy_name")
PROXY_PROTOCOL = get_base_config(FATE_FLOW_SERVICE_NAME, {}).get("protocol", "http")
PROXY = get_base_config("federation")
FORCE_USE_SQLITE = get_base_config("force_use_sqlite")
ENGINES = engine_utils.get_engines()
IS_STANDALONE = engine_utils.is_standalone()

DATABASE = decrypt_database_config()

# Logger
LoggerFactory.set_directory(os.path.join(get_fate_flow_directory(), "logs", "fate_flow"))
# {CRITICAL: 50, FATAL:50, ERROR:40, WARNING:30, WARN:30, INFO:20, DEBUG:10, NOTSET:0}
LoggerFactory.LEVEL = 10

IGNORE_RESOURCE_ROLES = {"arbiter"}

SUPPORT_IGNORE_RESOURCE_ENGINES = {
    ComputingEngine.EGGROLL, ComputingEngine.STANDALONE
}

HEADERS = {
    "Content-Type": "application/json",
    "Connection": "close",
    "service": FATE_FLOW_SERVICE_NAME
}

stat_logger = getLogger("fate_flow_stat")
detect_logger = getLogger("fate_flow_detect")
access_logger = getLogger("fate_flow_access")
database_logger = getLogger("fate_flow_database")

PARTY_ID = get_base_config("party_id", "")

SOURCE_MODEL_STORE_PATH = os.path.join(get_fate_flow_directory(), "model", "source")
CACHE_MODEL_STORE_PATH = os.path.join(get_fate_flow_directory(), "model", "cache")
LOCAL_DATA_STORE_PATH = os.path.join(get_fate_flow_directory(), "data")
BASE_URI = f"{PROTOCOL}://{HOST}:{HTTP_PORT}/{API_VERSION}"
