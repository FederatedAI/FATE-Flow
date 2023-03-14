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

from fate_flow.entity.types import ComputingEngine
from fate_flow.utils import engine_utils
from fate_flow.utils.conf_utils import get_base_config, decrypt_database_config
from fate_flow.utils.file_utils import get_project_base_directory
from fate_flow.utils.log_utils import LoggerFactory, getLogger

from fate_flow.settings import *

# Server
API_VERSION = "v2"
FATE_FLOW_SERVICE_NAME = "fateflow"
SERVER_MODULE = "fate_flow_server.py"
CASBIN_TABLE_NAME = "fate_casbin"
PERMISSION_MANAGER_PAGE = "permission"
APP_MANAGER_PAGE = "app"

ADMIN_PAGE = [PERMISSION_MANAGER_PAGE, APP_MANAGER_PAGE]
TEMP_DIRECTORY = os.path.join(get_fate_flow_directory(), "temp")
FATE_FLOW_CONF_PATH = os.path.join(get_fate_flow_directory(), "conf")

FATE_FLOW_JOB_DEFAULT_CONFIG_PATH = os.path.join(FATE_FLOW_CONF_PATH, "job_default_config.yaml")

SUBPROCESS_STD_LOG_NAME = "std.log"


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
WORKER = get_base_config("worker", {})
DEFAULT_PROVIDER = get_base_config("default_provider", {})
CASBIN_MODEL_CONF = os.path.join(FATE_FLOW_CONF_PATH, "casbin_model.conf")

DATABASE = decrypt_database_config()


IGNORE_RESOURCE_ROLES = {"arbiter"}

SUPPORT_IGNORE_RESOURCE_ENGINES = {
    ComputingEngine.EGGROLL, ComputingEngine.STANDALONE
}
DEFAULT_FATE_PROVIDER_PATH = get_project_base_directory("python")

HEADERS = {
    "Content-Type": "application/json",
    "Connection": "close",
    "service": FATE_FLOW_SERVICE_NAME
}

stat_logger = getLogger("fate_flow_stat")
detect_logger = getLogger("fate_flow_detect")
access_logger = getLogger("fate_flow_access")
database_logger = getLogger("fate_flow_database")

MODEL_STORE_PATH = os.path.join(get_fate_flow_directory(), "model")
LOCAL_DATA_STORE_PATH = os.path.join(get_fate_flow_directory(), "data")
BASE_URI = f"{PROTOCOL}://{HOST}:{HTTP_PORT}/{API_VERSION}"

HOOK_MODULE = get_base_config("hook_module")

# authentication
AUTHENTICATION_CONF = get_base_config("authentication", {})
# client
CLIENT_AUTHENTICATION = AUTHENTICATION_CONF.get("client", False)
# site
SITE_AUTHENTICATION = AUTHENTICATION_CONF.get("site", False)

PARTY_ID = get_base_config("party_id", "")
LOCAL_PARTY_ID = "0"

MODEL_STORE = get_base_config("model_store")