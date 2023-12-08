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
DAG_SCHEMA = "作业的定义和配置，包括多个任务的配置"
USER_NAME = "上层系统所提供的用户名"
JOB_ID = "作业ID"
ROLE = "参与方的角色: guest/host/arbiter/local"
STATUS = "作业或者任务的状态"
LIMIT = "限制条数或者行数"
PAGE = "页码数"
DESCRIPTION = "描述信息"
PARTNER = "参与方信息"
ORDER_BY = "排序的字段名"
ORDER = "排序方式：asc/desc"

# task
TASK_NAME = "任务名称"
TASK_ID = "任务ID"
TASK_VERSION = "任务版本"
NODES = "任务的标签等信息，用户可自定义化"

# data
SERVER_FILE_PATH = "服务器上的文件路径"
SERVER_DIR_PATH = "服务器上的目录路径"
HEAD = "文件的第一行是否为数据的Head"
PARTITIONS = "数据分区数量"
META = "数据的元信息"
EXTEND_SID = "是否需要自动填充一列作为数据行id"
NAMESPACE = "数据表的命名空间"
NAME = "数据表名"
DATA_WAREHOUSE = "数据输出，内容如:{name: xxx, namespace: xxx}"
DROP = "当数据存在时是否需要先销毁"
DOWNLOAD_HEADER = "是否需要下载数据的Head作为第一行"

# output
FILTERS = "过滤条件"
OUTPUT_KEY = "任务的输出数据或者模型的主键"

# table
DISPLAY = "是否需要返回预览数据"

# server
SERVER_NAME = "服务器名称"
SERVICE_NAME = "服务名称"
HOST = "主机ip"
PORT = "服务端口"
PROTOCOL = "协议：http/https"
URI = "服务路径"
METHOD = "请求方式：POST/GET等"
PARAMS = "请求头参数"
DATA = "请求体参数"
HEADERS = "请求头"

# provider
PROVIDER_NAME = "组件提供方名称"
DEVICE = "组件运行模式"
VERSION = "组件版本"
COMPONENT_METADATA = "组件注册详细信息"
COMPONENTS_DESCRIPTION = "组件描述"
PROVIDER_ALL_NAME = "注册的算法全名，提供方+':'+版本+'@'+运行模式，如: fate:2.0.0@local"

# permission
PERMISSION_APP_ID = "App id"
PERMISSION_ROLE = "权限名称"
COMPONENT = "组件名"
DATASET = "数据集列表"

# log
LOG_TYPE = "日志等级或类型"
INSTANCE_ID = "FATE Flow服务的实例ID"
BEGIN = "起始行号"
END = "结尾行号"


# site
PARTY_ID = "站点ID"

# model
MODEL_ID = "模型id"
MODEL_VERSION = "模型版本"

# app
APP_NAME = "客户端的app名称"
APP_ID = "客户端的app-id"
SITE_APP_ID = "站点的app-id"
SITE_APP_TOKEN = "站点的app-token"
