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

from .file_utils import load_yaml_conf, get_fate_flow_directory

SERVICE_CONF = "service_conf.yaml"
TRANSFER_CONF = "transfer_conf.yaml"


def conf_realpath(conf_name):
    conf_path = f"conf/{conf_name}"
    return os.path.join(get_fate_flow_directory(), conf_path)


def get_base_config(key, default=None, conf_name=SERVICE_CONF) -> dict:
    local_config = {}
    local_path = conf_realpath(f"local.{conf_name}")

    if os.path.exists(local_path):
        local_config = load_yaml_conf(local_path)
        if not isinstance(local_config, dict):
            raise ValueError(f'Invalid config file: "{local_path}".')

        if key is not None and key in local_config:
            return local_config[key]

    config_path = conf_realpath(conf_name)
    config = load_yaml_conf(config_path)

    if not isinstance(config, dict):
        raise ValueError(f'Invalid config file: "{config_path}".')

    config.update(local_config)
    return config.get(key, default) if key is not None else config
