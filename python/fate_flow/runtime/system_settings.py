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

from grpc._cython import cygrpc

from fate_flow.entity.types import ComputingEngine
from fate_flow.runtime.env import is_in_virtualenv
from fate_flow.utils import engine_utils, file_utils
from fate_flow.utils.conf_utils import get_base_config
from fate_flow.utils.file_utils import get_fate_flow_directory, get_fate_python_path

from fate_flow.settings import *

# Server
API_VERSION = "v2"
FATE_FLOW_SERVICE_NAME = "fateflow"
SERVER_MODULE = "fate_flow_server.py"
CASBIN_TABLE_NAME = "fate_casbin"
PERMISSION_TABLE_NAME = "permission_casbin"
PERMISSION_MANAGER_PAGE = "permission"
APP_MANAGER_PAGE = "app"

ADMIN_PAGE = [PERMISSION_MANAGER_PAGE, APP_MANAGER_PAGE]
FATE_FLOW_CONF_PATH = os.path.join(get_fate_flow_directory(), "conf")

FATE_FLOW_JOB_DEFAULT_CONFIG_PATH = os.path.join(FATE_FLOW_CONF_PATH, "job_default_config.yaml")

SUBPROCESS_STD_LOG_NAME = "std.log"


HOST = get_base_config(FATE_FLOW_SERVICE_NAME, {}).get("host", "127.0.0.1")
HTTP_PORT = get_base_config(FATE_FLOW_SERVICE_NAME, {}).get("http_port")
GRPC_PORT = get_base_config(FATE_FLOW_SERVICE_NAME, {}).get("grpc_port")

NGINX_HOST = get_base_config(FATE_FLOW_SERVICE_NAME, {}).get("nginx", {}).get("host") or HOST
NGINX_HTTP_PORT = get_base_config(FATE_FLOW_SERVICE_NAME, {}).get("nginx", {}).get("http_port") or HTTP_PORT
RANDOM_INSTANCE_ID = get_base_config(FATE_FLOW_SERVICE_NAME, {}).get("random_instance_id", False)

PROTOCOL = get_base_config(FATE_FLOW_SERVICE_NAME, {}).get("protocol", "http")

PROXY_NAME = get_base_config(FATE_FLOW_SERVICE_NAME, {}).get("proxy_name")
PROXY_PROTOCOL = get_base_config(FATE_FLOW_SERVICE_NAME, {}).get("protocol", "http")

THIRD_PARTY = get_base_config(FATE_FLOW_SERVICE_NAME, {}).get("third_party", None)

PROXY = get_base_config("federation")
STORAGE = get_base_config("storage")
ENGINES = engine_utils.get_engines()
IS_STANDALONE = engine_utils.is_standalone()
WORKER = get_base_config("worker", {})
DEFAULT_PROVIDER = get_base_config("default_provider", {})
CASBIN_MODEL_CONF = os.path.join(FATE_FLOW_CONF_PATH, "casbin_model.conf")
PERMISSION_CASBIN_MODEL_CONF = os.path.join(FATE_FLOW_CONF_PATH, "permission_casbin_model.conf")
SERVICE_CONF_NAME = "service_conf.yaml"

DATABASE = get_base_config("database", {})


IGNORE_RESOURCE_ROLES = {"arbiter"}

SUPPORT_IGNORE_RESOURCE_ENGINES = {
    ComputingEngine.EGGROLL, ComputingEngine.STANDALONE
}
DEFAULT_FATE_PROVIDER_PATH = (DEFAULT_FATE_DIR or get_fate_python_path()) if not is_in_virtualenv() else ""
HEADERS = {
    "Content-Type": "application/json",
    "Connection": "close",
    "service": FATE_FLOW_SERVICE_NAME
}

BASE_URI = f"{PROTOCOL}://{HOST}:{HTTP_PORT}/{API_VERSION}"

HOOK_MODULE = get_base_config("hook_module")
# computing
COMPUTING_CONF = get_base_config("computing", {})

# authentication
AUTHENTICATION_CONF = get_base_config("authentication", {})
# client
CLIENT_AUTHENTICATION = AUTHENTICATION_CONF.get("client", False)
# site
SITE_AUTHENTICATION = AUTHENTICATION_CONF.get("site", False)
# permission
PERMISSION_SWITCH = AUTHENTICATION_CONF.get("permission", False)

ENCRYPT_CONF = get_base_config("encrypt")

PARTY_ID = get_base_config("party_id", "")
LOCAL_PARTY_ID = "0"

MODEL_STORE = get_base_config("model_store")

GRPC_OPTIONS = [
    (cygrpc.ChannelArgKey.max_send_message_length, -1),
    (cygrpc.ChannelArgKey.max_receive_message_length, -1),
]

LOG_DIR = LOG_DIR or get_fate_flow_directory("logs")
JOB_DIR = JOB_DIR or get_fate_flow_directory("jobs")
MODEL_STORE_PATH = MODEL_DIR or os.path.join(get_fate_flow_directory(), "model")
LOCAL_DATA_STORE_PATH = DATA_DIR or os.path.join(get_fate_flow_directory(), "data")
LOG_LEVEL = LOG_LEVEL or 10
LOG_SHARE = False
FATE_FLOW_LOG_DIR = os.path.join(LOG_DIR, "fate_flow")
WORKERS_DIR = os.path.join(LOG_DIR, "workers")

SQLITE_FILE_DIR = SQLITE_FILE_DIR or get_fate_flow_directory()
SQLITE_PATH = os.path.join(SQLITE_FILE_DIR, SQLITE_FILE_NAME)

GRPC_SERVER_MAX_WORKERS = GRPC_SERVER_MAX_WORKERS or (os.cpu_count() or 1) * 5

VERSION_FILE_PATH = os.path.join(get_fate_flow_directory(), "fateflow.env")
FATE_FLOW_PROVIDER_PATH = get_fate_flow_directory("python")

# Registry
FATE_FLOW_MODEL_TRANSFER_ENDPOINT = "/v1/model/transfer"
ZOOKEEPER = get_base_config("zookeeper", {})
ZOOKEEPER_REGISTRY = {
    # server
    'flow-server': "/FATE-COMPONENTS/fate-flow",
    # model service
    'fateflow': "/FATE-SERVICES/flow/online/transfer/providers",
    'servings': "/FATE-SERVICES/serving/online/publishLoad/providers",
}
USE_REGISTRY = get_base_config("use_registry")

REQUEST_TRY_TIMES = 3
REQUEST_WAIT_SEC = 2
REQUEST_MAX_WAIT_SEC = 300

DEFAULT_OUTPUT_DATA_PARTITIONS = 16

STANDALONE_DATA_HOME = os.path.join(file_utils.get_fate_flow_directory(), "data")
LOCALFS_DATA_HOME = os.path.join(file_utils.get_fate_flow_directory(), "localfs")

# hub module settings
# define： xxx.class_name
DEFAULT_COMPONENTS_WRAPS_MODULE = "fate_flow.hub.components_wraps.fate.FlowWraps"
