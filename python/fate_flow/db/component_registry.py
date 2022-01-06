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
from fate_arch.common import file_utils
from fate_arch.common.versions import get_versions

from fate_flow.component_env_utils import provider_utils
from fate_flow.db.db_models import ComponentProviderInfo, ComponentRegistryInfo, ComponentInfo, DB
from fate_flow.db.runtime_config import RuntimeConfig
from fate_flow.entity import ComponentProvider
from fate_flow.entity.types import ComponentProviderName
from fate_flow.settings import FATE_FLOW_DEFAULT_COMPONENT_REGISTRY_PATH
from fate_flow.utils.log_utils import getLogger

LOGGER = getLogger()


class ComponentRegistry:
    REGISTRY = {}

    @classmethod
    def load(cls):
        component_registry = cls.get_from_db(file_utils.load_json_conf_real_time(FATE_FLOW_DEFAULT_COMPONENT_REGISTRY_PATH))
        cls.REGISTRY.update(component_registry)
        for provider_name, provider_info in cls.REGISTRY.get("providers", {}).items():
            if not ComponentProviderName.valid(provider_name):
                raise Exception(f"not support component provider: {provider_name}")
        cls.REGISTRY["providers"] = cls.REGISTRY.get("providers", {})
        cls.REGISTRY["components"] = cls.REGISTRY.get("components", {})
        RuntimeConfig.load_component_registry()

    @classmethod
    def register_provider(cls, provider: ComponentProvider):
        provider_interface = provider_utils.get_provider_interface(provider)
        support_components = provider_interface.get_names()
        components = {}
        for component_alias, info in support_components.items():
            component_name = component_alias.lower()
            if component_name not in components:
                components[component_name] = info
            elif components[component_name].get("module") != info.get("module"):
                raise ValueError(f"component {component_name} have different module info")
            components[component_name]["alias"] = components[component_name].get("alias", set())
            components[component_name]["alias"].add(component_alias)
        register_info = {
            "default": {
                "version": provider.version
            }
        }
        register_info = cls.get_providers().get(provider.name, register_info)
        register_info[provider.version] = {
                "path": provider.path,
                "class_path": provider.class_path,
                "components": components
        }
        cls.REGISTRY["providers"][provider.name] = register_info
        return components

    @classmethod
    def register_components(cls, provider: ComponentProvider, components: dict):
        for component_name, info in components.items():
            if component_name not in cls.REGISTRY["components"]:
                cls.REGISTRY["components"][component_name] = {
                    "default_provider": provider.name,
                    "support_provider": [],
                    "alias": info["alias"]
                }
            if provider.name not in cls.REGISTRY["components"][component_name]["support_provider"]:
                # do not use set because the json format is not supported
                cls.REGISTRY["components"][component_name]["support_provider"].append(provider.name)
                for component_alias in info["alias"]:
                    cls.REGISTRY["components"][component_alias] = cls.REGISTRY["components"][component_name]

    @classmethod
    def dump(cls):
        cls.save_to_db()

    @classmethod
    @DB.connection_context()
    def save_to_db(cls):
        # save component registry info
        with DB.lock("component_register"):
            for provider_name, provider_group_info in cls.REGISTRY["providers"].items():
                for version, version_register_info in provider_group_info.items():
                    if version != "default":
                        version_info = {
                            "f_path": version_register_info.get("path"),
                            "f_python": version_register_info.get("python", ""),
                            "f_class_path": version_register_info.get("class_path"),
                            "f_version": version,
                            "f_provider_name": provider_name
                        }
                        cls.safe_save(ComponentProviderInfo, version_info, f_version=version, f_provider_name=provider_name)
                        for component_name, component_info in version_register_info.get("components").items():
                            component_registry_info = {
                                "f_version": version,
                                "f_provider_name": provider_name,
                                "f_component_name": component_name,
                                "f_module": component_info.get("module")
                            }
                            cls.safe_save(ComponentRegistryInfo, component_registry_info, f_version=version,
                                          f_provider_name=provider_name, f_component_name=component_name)

            for component_name, info in cls.REGISTRY["components"].items():
                component_info = {
                    "f_component_name": component_name,
                    "f_default_provider": info.get("default_provider"),
                    "f_support_provider": info.get("support_provider"),
                    "f_component_alias": info.get("alias"),
                }
                cls.safe_save(ComponentInfo, component_info, f_component_name=component_name)

    @classmethod
    def safe_save(cls, model, defaults, **kwargs):
        entity_model, status = model.get_or_create(
            **kwargs,
            defaults=defaults)
        if status is False:
            for key in defaults:
                setattr(entity_model, key, defaults[key])
            entity_model.save(force_insert=False)

    @classmethod
    @DB.connection_context()
    def get_from_db(cls, component_registry):
        # get component registry info
        component_list = ComponentInfo.select()
        for component in component_list:
            component_registry["components"][component.f_component_name] = {
                "default_provider": component.f_default_provider,
                "support_provider": component.f_support_provider,
                "alias": component.f_component_alias
            }
            for component_alias in component.f_component_alias:
                component_registry["components"][component_alias] = component_registry["components"][component.f_component_name]

        provider_list = ComponentProviderInfo.select()

        # get key names from `fateflow/conf/component_registry.json`
        default_version_keys = {
            provider_name: default_settings["default_version_key"]
            for provider_name, default_settings in component_registry["default_settings"].items()
            if "default_version_key" in default_settings
        }

        for provider_info in provider_list:
            if provider_info.f_provider_name not in component_registry["providers"]:
                component_registry["providers"][provider_info.f_provider_name] = {
                    "default": {
                        "version": get_versions()[default_version_keys[provider_info.f_provider_name]]
                        if provider_info.f_provider_name in default_version_keys else provider_info.f_version,
                    }
                }

            component_registry["providers"][provider_info.f_provider_name][provider_info.f_version] = {
                "path": provider_info.f_path,
                "python": provider_info.f_python,
                "class_path": provider_info.f_class_path
            }
            modules_list = ComponentRegistryInfo.select().where(
                ComponentRegistryInfo.f_provider_name == provider_info.f_provider_name,
                ComponentRegistryInfo.f_version == provider_info.f_version
            )
            modules = {}
            for module in modules_list:
                modules[module.f_component_name] = {"module": module.f_module}
                for component_alias in component_registry["components"][module.f_component_name]["alias"]:
                    modules[component_alias] = modules[module.f_component_name]
            component_registry["providers"][provider_info.f_provider_name][provider_info.f_version]["components"] = modules
        return component_registry

    @classmethod
    def get_providers(cls):
        return cls.REGISTRY.get("providers", {})

    @classmethod
    def get_components(cls):
        return cls.REGISTRY.get("components", {})

    @classmethod
    def get_provider_components(cls, provider_name, provider_version):
        return cls.get_providers()[provider_name][provider_version]["components"]

    @classmethod
    def get_default_class_path(cls):
        return ComponentRegistry.REGISTRY["default_settings"]["class_path"]

