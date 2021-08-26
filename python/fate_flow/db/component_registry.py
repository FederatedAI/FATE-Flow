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

from fate_arch.common import file_utils
from fate_flow.component_env_utils import provider_utils
from fate_flow.entity.component_provider import ComponentProvider
from fate_flow.entity.types import ComponentProviderName
from fate_flow.settings import FATE_FLOW_DEFAULT_COMPONENT_REGISTRY_PATH, \
    FATE_FLOW_DEFAULT_COMPONENT_REGISTRY_PATH_REALTIME


class ComponentRegistry:
    REGISTRY = {}

    @classmethod
    def load(cls):
        # todo: use database instead of file, and add lock
        if os.path.exists(FATE_FLOW_DEFAULT_COMPONENT_REGISTRY_PATH_REALTIME):
            component_registry = file_utils.load_json_conf(FATE_FLOW_DEFAULT_COMPONENT_REGISTRY_PATH_REALTIME)
        else:
            component_registry = file_utils.load_json_conf(FATE_FLOW_DEFAULT_COMPONENT_REGISTRY_PATH)
        cls.REGISTRY.update(component_registry)
        for provider_name, provider_info in cls.REGISTRY.get("provider", {}).items():
            if not ComponentProviderName.contains(provider_name):
                raise Exception(f"not support component provider: {provider_name}")
        cls.REGISTRY["provider"] = cls.REGISTRY.get("provider", {})
        cls.REGISTRY["components"] = cls.REGISTRY.get("components", {})

    @classmethod
    def register_provider(cls, provider: ComponentProvider):
        provider_interface = provider_utils.get_provider_interface(provider)
        support_components = provider_interface.get_names()
        register_info = {
            "default": {
                "version": provider.version
            }
        }
        register_info = cls.REGISTRY["provider"].get(provider.name, register_info)
        register_info[provider.version] = {
                "path": provider.path,
                "class_path": provider.class_path,
                "components": support_components
        }
        cls.REGISTRY["provider"][provider.name] = register_info
        return support_components

    @classmethod
    def register_components(cls, provider: ComponentProvider, components):
        for _cpn in components.keys():
            cls.REGISTRY["components"][_cpn] = cls.REGISTRY["components"].get(_cpn,
                                                                              {
                                                                                  "default_provider": provider.name, "support_provider": []
                                                                              })
            if provider.name not in cls.REGISTRY["components"][_cpn]["support_provider"]:
                # do not use set because the json format is not supported
                cls.REGISTRY["components"][_cpn]["support_provider"].append(provider.name)

    @classmethod
    def dump(cls):
        # todo: use database instead of file, and add lock
        file_utils.rewrite_json_file(FATE_FLOW_DEFAULT_COMPONENT_REGISTRY_PATH_REALTIME, cls.REGISTRY)

    @classmethod
    def get_provider_components(cls, provider_name, provider_version):
        return cls.REGISTRY["provider"][provider_name][provider_version]["components"]

    @classmethod
    def get_default_class_path(cls):
        return ComponentRegistry.REGISTRY["default_settings"]["class_path"]

