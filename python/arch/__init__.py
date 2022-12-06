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
from fate.arch.common.file_utils import get_project_base_directory, load_json_conf
from fate.arch.common.versions import get_versions
from fate.arch.metastore.db_models import init_database_tables as init_arch_db
from fate.arch.protobuf.python import proxy_pb2_grpc, basic_meta_pb2, proxy_pb2
from fate.arch.common.conf_utils import get_base_config, decrypt_database_config
from fate.arch.computing import ComputingEngine
from fate.arch.common.base_utils import current_timestamp, fate_uuid, json_dumps, json_loads, CustomJSONEncoder
from fate.arch.common import CoordinationProxyService, engine_utils, BaseType, FederatedMode, file_utils, EngineType
from fate.arch.metastore.base_model import BaseModel, SerializedField, SerializedType, JSONField, \
    auto_date_timestamp_db_field