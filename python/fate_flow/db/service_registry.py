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
import socket
from pathlib import Path
from fate_arch.common import file_utils, conf_utils
from fate_arch.common.conf_utils import SERVICE_CONF
from .reload_config_base import ReloadConfigBase


class ServiceRegistry(ReloadConfigBase):
    FATEBOARD = None
    FATE_ON_STANDALONE = None
    FATE_ON_EGGROLL = None
    FATE_ON_SPARK = None
    MODEL_STORE_ADDRESS = None
    SERVINGS = None
    FATEMANAGER = None
    STUDIO = None

    @classmethod
    def load(cls):
        path = Path(file_utils.get_project_base_directory()) / 'conf' / SERVICE_CONF
        conf = file_utils.load_yaml_conf(path)
        if not isinstance(conf, dict):
            raise ValueError('invalid config file')

        local_path = path.with_name(f'local.{SERVICE_CONF}')
        if local_path.exists():
            local_conf = file_utils.load_yaml_conf(local_path)
            if not isinstance(local_conf, dict):
                raise ValueError('invalid local config file')
            conf.update(local_conf)

        cls.LINKIS_SPARK_CONFIG = conf.get('fate_on_spark', {}).get('linkis_spark')

        for k, v in conf.items():
            if isinstance(v, dict):
                setattr(cls, k.upper(), v)

    @classmethod
    def register(cls, service_name, service_config):
        setattr(cls, service_name, service_config)


    @classmethod
    def save(cls, service_config):
        update_server = {}
        for service_name, service_info in service_config.items():
            cls.parameter_verification(service_name, service_info)
            manager_conf = conf_utils.get_base_config(service_name, {})
            if not manager_conf:
                manager_conf = service_info
            else:
                manager_conf.update(service_info)
            conf_utils.update_config(service_name, manager_conf)
            update_server[service_name] = manager_conf
            setattr(cls, service_name.upper(), manager_conf)
        return update_server

    @classmethod
    def parameter_verification(cls,service_name, service_info):
        registry_service_info = {
            "fatemanager": ["host", "port", "federatedId"],
            "studio": ["host", "port"]
        }
        if service_name not in registry_service_info.keys():
            raise Exception(f"service {service_name} cannot be registered")
        if set(service_info.keys()) != set(registry_service_info.get(service_name)):
            raise Exception(f'the registration service {service_name} configuration item is'
                            f' {registry_service_info.get(service_name)}')
        if "host" in service_info and "port" in service_info:
            cls.connection_test(service_info.get("host"), service_info.get("port"))


    @classmethod
    def connection_test(cls, ip, port):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = s.connect_ex((ip, port))
        if result != 0:
            raise ConnectionRefusedError(f"connection refused: host {ip}, port {port}")

    @classmethod
    def query(cls, service_name, default=None):
        service_info = getattr(cls, service_name, default)
        if not service_info:
            service_info = conf_utils.get_base_config(service_name, default)
        return service_info
