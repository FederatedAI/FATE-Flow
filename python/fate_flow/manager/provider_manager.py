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
import os.path
import sys
from copy import deepcopy

from fate_arch.common import file_utils
from fate_arch.common.versions import get_versions
from fate_flow.entity import ComponentProvider
from fate_flow.db.component_registry import ComponentRegistry
from fate_flow.db.job_default_config import JobDefaultConfig
from fate_flow.manager.worker_manager import WorkerManager
from fate_flow.entity.types import WorkerName
from fate_flow.settings import stat_logger
from fate_flow.utils.base_utils import get_fate_flow_python_directory


class ProviderManager:
    @classmethod
    def register_default_providers(cls):
        code, result = cls.register_fate_flow_provider()
        if code != 0:
            raise Exception(f"register fate flow tools component failed")
        code, result, provider = cls.register_default_fate_provider()
        if code != 0:
            raise Exception(f"register default fate algorithm component failed")
        return provider

    @classmethod
    def register_fate_flow_provider(cls):
        provider = cls.get_fate_flow_provider()
        return WorkerManager.start_general_worker(worker_name=WorkerName.PROVIDER_REGISTRAR, provider=provider, run_in_subprocess=False)

    @classmethod
    def register_default_fate_provider(cls):
        provider = cls.get_default_fate_provider()
        sys.path.append(provider.env["PYTHONPATH"])
        code, result = WorkerManager.start_general_worker(worker_name=WorkerName.PROVIDER_REGISTRAR, provider=provider, run_in_subprocess=False)
        return code, result, provider

    @classmethod
    def get_fate_flow_provider(cls):
        path = get_fate_flow_python_directory("fate_flow")
        provider = ComponentProvider(name="fate_flow", version=get_versions()["FATEFlow"], path=path, class_path=ComponentRegistry.get_default_class_path())
        return provider

    @classmethod
    def get_default_fate_provider_env(cls):
        provider = cls.get_default_fate_provider()
        return provider.env

    @classmethod
    def get_default_fate_provider(cls):
        path = JobDefaultConfig.default_component_provider_path.split("/")
        path = file_utils.get_fate_python_directory(*path)
        if not os.path.exists(path):
            raise Exception(f"default fate provider not exists: {path}")
        provider = ComponentProvider(name="fate", version=get_versions()["FATE"], path=path, class_path=ComponentRegistry.get_default_class_path())
        return provider

    @classmethod
    def if_default_provider(cls, provider: ComponentProvider):
        if provider == cls.get_fate_flow_provider() or provider == cls.get_default_fate_provider():
            return True
        else:
            return False

    @classmethod
    def fill_fate_flow_provider(cls, dsl):
        dest_dsl = deepcopy(dsl)
        fate_flow_provider = cls.get_fate_flow_provider()
        support_components = ComponentRegistry.get_provider_components(fate_flow_provider.name, fate_flow_provider.version)
        provider_key = f"{fate_flow_provider.name}@{fate_flow_provider.version}"
        for cpn, config in dsl["components"].items():
            if config["module"] in support_components:
                dest_dsl["components"][cpn]["provider"] = provider_key
        return dest_dsl

    @classmethod
    def get_fate_flow_component_module(cls):
        fate_flow_provider = cls.get_fate_flow_provider()
        return ComponentRegistry.get_provider_components(fate_flow_provider.name, fate_flow_provider.version)

    @classmethod
    def get_provider_object(cls, provider_info, check_registration=True):
        name, version = provider_info["name"], provider_info["version"]
        if check_registration and ComponentRegistry.get_providers().get(name, {}).get(version, None) is None:
            raise Exception(f"{name} {version} provider is not registered")
        path = ComponentRegistry.get_providers().get(name, {}).get(version, {}).get("path", [])
        class_path = ComponentRegistry.get_providers().get(name, {}).get(version, {}).get("class_path", None)
        if class_path is None:
            class_path = ComponentRegistry.REGISTRY["default_settings"]["class_path"]
        return ComponentProvider(name=name, version=version, path=path, class_path=class_path)

    @classmethod
    def get_job_provider_group(cls, dsl_parser, components: list = None, check_registration=True):
        providers_info = dsl_parser.get_job_providers(provider_detail=ComponentRegistry.REGISTRY)
        group = {}
        if components is not None:
            _providers_info = {}
            for component_name in components:
                _providers_info[component_name] = providers_info.get(component_name)
            providers_info = _providers_info
        for component_name, provider_info in providers_info.items():
            provider = cls.get_provider_object(provider_info["provider"], check_registration=check_registration)
            group_key = "@".join([provider.name, provider.version])
            if group_key not in group:
                group[group_key] = {
                    "provider": provider.to_dict(),
                    "if_default_provider": cls.if_default_provider(provider),
                    "components": [component_name]
                }
            else:
                group[group_key]["components"].append(component_name)
        return group

    @classmethod
    def get_component_provider(cls, dsl_parser, component_name):
        providers = dsl_parser.get_job_providers(provider_detail=ComponentRegistry.REGISTRY)
        return cls.get_provider_object(providers[component_name]["provider"])

    @classmethod
    def get_component_parameters(cls, dsl_parser, component_name, role, party_id, provider: ComponentProvider = None, previous_components_parameters: dict = None):
        if not provider:
            provider = cls.get_component_provider(dsl_parser=dsl_parser,
                                                  component_name=component_name)
        parameters = dsl_parser.parse_component_parameters(component_name,
                                                           ComponentRegistry.REGISTRY,
                                                           provider.name,
                                                           provider.version,
                                                           local_role=role,
                                                           local_party_id=int(party_id))
        user_specified_parameters = dsl_parser.parse_user_specified_component_parameters(component_name,
                                                                                         ComponentRegistry.REGISTRY,
                                                                                         provider.name,
                                                                                         provider.version,
                                                                                         local_role=role,
                                                                                         local_party_id=int(party_id),
                                                                                         previous_parameters=previous_components_parameters)
        return parameters, user_specified_parameters

    @classmethod
    def get_component_run_info(cls, dsl_parser, component_name, role, party_id, previous_components_parameters: dict = None):
        provider = cls.get_component_provider(dsl_parser, component_name)
        parameters, user_specified_parameters = cls.get_component_parameters(dsl_parser, component_name, role, party_id, provider, previous_components_parameters)
        return provider, parameters, user_specified_parameters
