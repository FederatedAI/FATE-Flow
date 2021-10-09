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
from fate_flow.entity import ComponentProvider
from fate_flow.db.component_registry import ComponentRegistry
from fate_flow.manager.worker_manager import WorkerManager
from fate_flow.entity.types import WorkerName


class ProviderManager:
    @classmethod
    def register_default_providers(cls):
        code, std = cls.register_fate_flow_component_provider()
        if code != 0:
            raise Exception(f"register fate flow tools component failed")
        code, std = cls.register_default_fate_algorithm_component_provider()
        if code != 0:
            raise Exception(f"register default fate algorithm component failed")

    @classmethod
    def register_fate_flow_component_provider(cls):
        path = file_utils.get_python_base_directory("fate_flow")
        provider = ComponentProvider(name="fate_flow_tools", version=get_versions()["FATEFlow"], path=path, class_path=ComponentRegistry.get_default_class_path())
        return WorkerManager.start_general_worker(worker_name=WorkerName.PROVIDER_REGISTRAR, provider=provider)

    @classmethod
    def register_default_fate_algorithm_component_provider(cls):
        path = ["component_plugins",
                "fate",
                "python",
                "federatedml"]
        path = file_utils.get_python_base_directory(*path)
        provider = ComponentProvider(name="fate_algorithm", version=get_versions()["FATE"], path=path, class_path=ComponentRegistry.get_default_class_path())
        return WorkerManager.start_general_worker(worker_name=WorkerName.PROVIDER_REGISTRAR, provider=provider)

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
            group_key = ":".join([provider.name, provider.version])
            if group_key not in group:
                group[group_key] = {
                    "provider": provider.to_dict(),
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
    def get_component_run_info(cls, dsl_parser, component_name, role, party_id):
        provider = cls.get_component_provider(dsl_parser, component_name)
        parameters, user_specified_parameters = cls.get_component_parameters(dsl_parser, component_name, role, party_id, provider)
        return provider, parameters, user_specified_parameters
