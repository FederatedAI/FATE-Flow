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

from fate_arch.computing import ComputingEngine
from fate_arch.common import engine_utils
from fate_arch.common.conf_utils import get_base_config, decrypt_database_config
from fate_flow.utils.base_utils import get_fate_flow_directory
from fate_flow.utils.log_utils import LoggerFactory, getLogger


# Server
API_VERSION = "v1"
FATE_ENV_KEY_LIST = ['FATE', 'FATEFlow', 'FATEBoard', 'EGGROLL', 'CENTOS', 'UBUNTU', 'PYTHON', 'MAVEN', 'JDK', 'SPARK']
FATE_FLOW_SERVICE_NAME = "fateflow"
SERVER_MODULE = "fate_flow_server.py"
CASBIN_TABLE_NAME = "fate_casbin"
TEMP_DIRECTORY = os.path.join(get_fate_flow_directory(), "temp")
FATE_FLOW_CONF_PATH = os.path.join(get_fate_flow_directory(), "conf")

FATE_FLOW_JOB_DEFAULT_CONFIG_PATH = os.path.join(FATE_FLOW_CONF_PATH, "job_default_config.yaml")
FATE_FLOW_DEFAULT_COMPONENT_REGISTRY_PATH = os.path.join(FATE_FLOW_CONF_PATH, "component_registry.json")
TEMPLATE_INFO_PATH = os.path.join(FATE_FLOW_CONF_PATH, "template_info.yaml")
FATE_VERSION_DEPENDENCIES_PATH = os.path.join(get_fate_flow_directory(), "version_dependencies")
CASBIN_MODEL_CONF = os.path.join(FATE_FLOW_CONF_PATH, "casbin_model.conf")
INCOMPATIBLE_VERSION_CONF = os.path.join(FATE_FLOW_CONF_PATH, "incompatible_version.yaml")
SUBPROCESS_STD_LOG_NAME = "std.log"

GRPC_SERVER_MAX_WORKERS = None
MAX_TIMESTAMP_INTERVAL = 60

ERROR_REPORT = True
ERROR_REPORT_WITH_PATH = False

SESSION_VALID_PERIOD = 7 * 24 * 60 * 60 * 1000

REQUEST_TRY_TIMES = 3
REQUEST_WAIT_SEC = 2
REQUEST_MAX_WAIT_SEC = 300

USE_REGISTRY = get_base_config("use_registry")

# distribution
DEPENDENT_DISTRIBUTION = get_base_config("dependent_distribution", False)
FATE_FLOW_UPDATE_CHECK = False

HOST = get_base_config(FATE_FLOW_SERVICE_NAME, {}).get("host", "127.0.0.1")
HTTP_PORT = get_base_config(FATE_FLOW_SERVICE_NAME, {}).get("http_port")
GRPC_PORT = get_base_config(FATE_FLOW_SERVICE_NAME, {}).get("grpc_port")

NGINX_HOST = get_base_config(FATE_FLOW_SERVICE_NAME, {}).get("nginx", {}).get("host") or HOST
NGINX_HTTP_PORT = get_base_config(FATE_FLOW_SERVICE_NAME, {}).get("nginx", {}).get("http_port") or HTTP_PORT
NGINX_GRPC_PORT = get_base_config(FATE_FLOW_SERVICE_NAME, {}).get("nginx", {}).get("grpc_port") or GRPC_PORT

RANDOM_INSTANCE_ID = get_base_config(FATE_FLOW_SERVICE_NAME, {}).get("random_instance_id", False)

PROXY = get_base_config(FATE_FLOW_SERVICE_NAME, {}).get("proxy")
PROXY_PROTOCOL = get_base_config(FATE_FLOW_SERVICE_NAME, {}).get("protocol")

ENGINES = engine_utils.get_engines()
IS_STANDALONE = engine_utils.is_standalone()

DATABASE = decrypt_database_config()
ZOOKEEPER = get_base_config("zookeeper", {})

# Registry
ZOOKEEPER_REGISTRY = {
    # server
    'flow-server': "/FATE-COMPONENTS/fate-flow",
    # model service
    'fateflow': "/FATE-SERVICES/flow/online/transfer/providers",
    'servings': "/FATE-SERVICES/serving/online/publishLoad/providers",
}

# Engine
IGNORE_RESOURCE_COMPUTING_ENGINE = {
    ComputingEngine.LINKIS_SPARK
}

IGNORE_RESOURCE_ROLES = {"arbiter"}

SUPPORT_IGNORE_RESOURCE_ENGINES = {
    ComputingEngine.EGGROLL, ComputingEngine.STANDALONE
}

# linkis spark config
LINKIS_EXECUTE_ENTRANCE = "/api/rest_j/v1/entrance/execute"
LINKIS_KILL_ENTRANCE = "/api/rest_j/v1/entrance/execID/kill"
LINKIS_QUERT_STATUS = "/api/rest_j/v1/entrance/execID/status"
LINKIS_SUBMIT_PARAMS = {
    "configuration": {
        "startup": {
            "spark.python.version": "/data/anaconda3/bin/python",
            "archives": "hdfs:///apps-data/fate/python.zip#python,hdfs:///apps-data/fate/fate_guest.zip#fate_guest",
            "spark.executorEnv.PYTHONPATH": "./fate_guest/python:$PYTHONPATH",
            "wds.linkis.rm.yarnqueue": "dws",
            "spark.pyspark.python": "python/bin/python"
        }
    }
}
LINKIS_RUNTYPE = "py"
LINKIS_LABELS = {"tenant": "fate"}

# Endpoint
FATE_FLOW_MODEL_TRANSFER_ENDPOINT = "/v1/model/transfer"
FATE_MANAGER_GET_NODE_INFO_ENDPOINT = "/fate-manager/api/site/secretinfo"
FATE_MANAGER_NODE_CHECK_ENDPOINT = "/fate-manager/api/site/checksite"
FATE_BOARD_DASHBOARD_ENDPOINT = "/index.html#/dashboard?job_id={}&role={}&party_id={}"

# Logger
LoggerFactory.set_directory(os.path.join(get_fate_flow_directory(), "logs", "fate_flow"))
# {CRITICAL: 50, FATAL:50, ERROR:40, WARNING:30, WARN:30, INFO:20, DEBUG:10, NOTSET:0}
LoggerFactory.LEVEL = 10

stat_logger = getLogger("fate_flow_stat")
detect_logger = getLogger("fate_flow_detect")
access_logger = getLogger("fate_flow_access")
database_logger = getLogger("fate_flow_database")

# Switch
# upload
UPLOAD_DATA_FROM_CLIENT = True

# authentication
AUTHENTICATION_CONF = get_base_config("authentication", {})

PARTY_ID = get_base_config("party_id", "")

# client
CLIENT_AUTHENTICATION = AUTHENTICATION_CONF.get("client", {}).get("switch", False)
HTTP_APP_KEY = AUTHENTICATION_CONF.get("client", {}).get("http_app_key")
HTTP_SECRET_KEY = AUTHENTICATION_CONF.get("client", {}).get("http_secret_key")

# site
SITE_AUTHENTICATION = AUTHENTICATION_CONF.get("site", {}).get("switch", False)

# permission
PERMISSION_CONF = get_base_config("permission", {})
PERMISSION_SWITCH = PERMISSION_CONF.get("switch")
COMPONENT_PERMISSION = PERMISSION_CONF.get("component")
DATASET_PERMISSION = PERMISSION_CONF.get("dataset")

HOOK_MODULE = get_base_config("hook_module")
HOOK_SERVER_NAME = get_base_config("hook_server_name")

ENABLE_MODEL_STORE = get_base_config('enable_model_store', False)
