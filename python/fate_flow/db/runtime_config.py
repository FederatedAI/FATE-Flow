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
from fate_arch.common.versions import get_versions
from fate_arch.common import file_utils
from fate_flow.settings import FATE_FLOW_DEFAULT_COMPONENT_REGISTRY_PATH, FATE_FLOW_DEFAULT_COMPONENT_REGISTRY_PATH_REALTIME
from fate_flow.entity.types import ComponentProviderName, ProcessRole
from fate_flow.entity.component_provider import ComponentProvider
from .reload_config_base import ReloadConfigBase


class RuntimeConfig(ReloadConfigBase):
    WORK_MODE = None
    COMPUTING_ENGINE = None
    FEDERATION_ENGINE = None
    FEDERATED_MODE = None

    JOB_QUEUE = None
    USE_LOCAL_DATABASE = False
    HTTP_PORT = None
    JOB_SERVER_HOST = None
    JOB_SERVER_VIP = None
    IS_SERVER = False
    PROCESS_ROLE = None
    ENV = dict()
    COMPONENT_REGISTRY = {}
    COMPONENT_PROVIDER: ComponentProvider = None

    @classmethod
    def init_config(cls, **kwargs):
        for k, v in kwargs.items():
            if hasattr(cls, k):
                setattr(cls, k, v)

    @classmethod
    def init_env(cls):
        cls.ENV.update(get_versions())

    @classmethod
    def get_env(cls, key):
        return cls.ENV.get(key, None)

    @classmethod
    def get_all_env(cls):
        return cls.ENV

    @classmethod
    def set_process_role(cls, process_role: ProcessRole):
        cls.PROCESS_ROLE = process_role

    @classmethod
    def set_component_provider(cls, component_provider: ComponentProvider):
        cls.COMPONENT_PROVIDER = component_provider

    @classmethod
    def load_component_registry(cls):
        if os.path.exists(FATE_FLOW_DEFAULT_COMPONENT_REGISTRY_PATH_REALTIME):
            component_registry = file_utils.load_json_conf(FATE_FLOW_DEFAULT_COMPONENT_REGISTRY_PATH_REALTIME)
        else:
            component_registry = file_utils.load_json_conf(FATE_FLOW_DEFAULT_COMPONENT_REGISTRY_PATH)
        RuntimeConfig.COMPONENT_REGISTRY.update(component_registry)
        for provider_name, provider_info in component_registry.get("provider", {}).items():
            if not ComponentProviderName.contains(provider_name):
                del RuntimeConfig.COMPONENT_REGISTRY["provider"][provider_name]
                raise Exception(f"not support component provider: {provider_name}")
        RuntimeConfig.COMPONENT_REGISTRY["provider"] = RuntimeConfig.COMPONENT_REGISTRY.get("provider", {})
        RuntimeConfig.COMPONENT_REGISTRY["components"] = RuntimeConfig.COMPONENT_REGISTRY.get("components", {})

    @classmethod
    def register_default_providers(cls):
        provider_name, support_components = cls.register_fate_flow_component_provider()
        cls.register_components(provider_name, support_components)
        provider_name, support_components = cls.register_default_fate_algorithm_component_provider()
        cls.register_components(provider_name, support_components)

    @classmethod
    def register_fate_flow_component_provider(cls):
        provider_version = get_versions()["FATEFlow"]
        provider_name = "fate_flow_tools"
        from fate_flow.components.components import Components
        support_components = Components.get_names()
        fate_flow_tool_component_provider = {
            "default": {
                "version": provider_version
            },
            provider_version: {
                "path": ["fate_flow"],
                "components": support_components
            }
        }
        RuntimeConfig.COMPONENT_REGISTRY["provider"][provider_name] = fate_flow_tool_component_provider
        return provider_name, support_components

    @classmethod
    def register_default_fate_algorithm_component_provider(cls):
        provider_version = get_versions()["FATE"]
        provider_name = "fate_algorithm"
        from federatedml.components.components import Components
        support_components = Components.get_names()
        fate_algorithm_component_provider = {
            "default": {
                "version": provider_version
            },
            provider_version: {
                "path": ["component_plugins",
                          "fate",
                          "python",
                          "federatedml"],
                "components": support_components
            }
        }
        RuntimeConfig.COMPONENT_REGISTRY["provider"][provider_name] = fate_algorithm_component_provider
        return provider_name, support_components

    @classmethod
    def register_components(cls, provider_name, components):
        for _cpn in components.keys():
            RuntimeConfig.COMPONENT_REGISTRY["components"][_cpn] = RuntimeConfig.COMPONENT_REGISTRY["components"].get(_cpn, {"default_provider": "", "support_provider": []})
            if provider_name not in RuntimeConfig.COMPONENT_REGISTRY["components"][_cpn]["support_provider"]:
                #do not use set because the json format is not supported
                RuntimeConfig.COMPONENT_REGISTRY["components"][_cpn]["support_provider"].append(provider_name)
            RuntimeConfig.COMPONENT_REGISTRY["components"][_cpn]["default_provider"] = provider_name

    @classmethod
    def dump_component_registry(cls):
        file_utils.rewrite_json_file(FATE_FLOW_DEFAULT_COMPONENT_REGISTRY_PATH_REALTIME, RuntimeConfig.COMPONENT_REGISTRY)

    @classmethod
    def get_provider_components(cls, provider_name, provider_version):
        return RuntimeConfig.COMPONENT_REGISTRY["provider"][provider_name][provider_version]["components"]
