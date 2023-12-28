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

# job
DAG_SCHEMA = "Definition and configuration of jobs, including the configuration of multiple tasks"
USER_NAME = "Username provided by the upper-level system"
JOB_ID = "Job ID"
ROLE = "Role of the participant: guest/host/arbiter/local"
STATUS = "Status of the job or task"
LIMIT = "Limit of rows or entries"
PAGE = "Page number"
DESCRIPTION = "Description information"
PARTNER = "Participant information"
ORDER_BY = "Field name for sorting"
ORDER = "Sorting order: asc/desc"

# task
TASK_NAME = "Task name"
TASK_ID = "Task ID"
TASK_VERSION = "Task version"
NODES = "Tags and customizable information for tasks"

# data
SERVER_FILE_PATH = "File path on the server"
SERVER_DIR_PATH = "Directory path on the server"
HEAD = "Whether the first row of the file is the data's head"
PARTITIONS = "Number of data partitions"
META = "Metadata of the data"
EXTEND_SID = "Whether to automatically fill a column as data row ID"
NAMESPACE = "Namespace of the data table"
NAME = "Name of the data table"
SITE_NAME = "Site name"
DATA_WAREHOUSE = "Data output, content like: {name: xxx, namespace: xxx}"
DROP = "Whether to destroy data if it already exists"
DOWNLOAD_HEADER = "Whether to download the data's head as the first row"

# output
FILTERS = "Filter conditions"
OUTPUT_KEY = "Primary key for output data or model of the task"

# table
DISPLAY = "Whether to return preview data"

# server
SERVER_NAME = "Server name"
SERVICE_NAME = "Service name"
HOST = "Host IP"
PORT = "Service port"
PROTOCOL = "Protocol: fate/bfia,etc."
URI = "Service path"
METHOD = "Request method: POST/GET, etc."
PARAMS = "Request header parameters"
DATA = "Request body parameters"
HEADERS = "Request headers"

# provider
PROVIDER_NAME = "Component provider name"
DEVICE = "Component running mode"
VERSION = "Component version"
COMPONENT_METADATA = "Detailed information about component registration"
COMPONENTS_DESCRIPTION = "Components description"
PROVIDER_ALL_NAME = "Registered algorithm full name, provider + ':' + version + '@' + running mode, e.g., fate:2.0.0@local"

# permission
PERMISSION_APP_ID = "App ID"
PERMISSION_ROLE = "Permission name"
COMPONENT = "Component name"
DATASET = "List of datasets"

# log
LOG_TYPE = "Log level or type"
INSTANCE_ID = "Instance ID of the FATE Flow service"
BEGIN = "Starting line number"
END = "Ending line number"

# site
PARTY_ID = "Site ID"

# model
MODEL_ID = "Model ID"
MODEL_VERSION = "Model version"

# app
APP_NAME = "App name for the client"
APP_ID = "App ID for the client"
SITE_APP_ID = "App ID for the site"
SITE_APP_TOKEN = "App token for the site"
