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
import sys
from typing import Union

from fate_flow.db import ProviderInfo, ComponentInfo
from fate_flow.db.base_models import DB, BaseModelOperate
from fate_flow.entity.spec.flow import ProviderSpec, LocalProviderSpec, DockerProviderSpec, K8sProviderSpec
from fate_flow.entity.types import ProviderDevice, PROTOCOL
from fate_flow.hub.flow_hub import FlowHub
from fate_flow.hub.provider import EntrypointABC
from fate_flow.runtime.system_settings import DEFAULT_FATE_PROVIDER_PATH, DEFAULT_PROVIDER, FATE_FLOW_PROVIDER_PATH
from fate_flow.runtime.component_provider import ComponentProvider
from fate_flow.utils.log import getLogger
from fate_flow.utils.version import get_versions, get_default_fate_version, get_flow_version
from fate_flow.utils.wraps_utils import filter_parameters

stat_logger = getLogger("fate_flow_stat")


class ProviderManager(BaseModelOperate):
    @classmethod
    def get_provider_by_provider_name(cls, provider_name) -> ComponentProvider:
        name, version, device = cls.parser_provider_name(provider_name)
        provider_list = [provider_info for provider_info in cls.query_provider(name=name, version=version, device=device)]
        if not provider_list:
            raise ValueError(f"Query provider info failed: {provider_name}")
        provider_info = provider_list[0]
        return cls.get_provider(provider_info.f_name, provider_info.f_device, provider_info.f_version,
                                provider_info.f_metadata)

    @classmethod
    def get_provider(cls, name, device, version, metadata, check=False) -> Union[ComponentProvider, None]:
        if device == ProviderDevice.LOCAL:
            metadata = LocalProviderSpec(check, **metadata)
        elif device == ProviderDevice.DOCKER:
            metadata = DockerProviderSpec(check, **metadata)
        elif device == ProviderDevice.K8S:
            metadata = K8sProviderSpec(check, **metadata)
        else:
            return None
        return ComponentProvider(ProviderSpec(name=name, device=device, version=version, metadata=metadata))

    @classmethod
    @DB.connection_context()
    def register_provider(cls, provider: ComponentProvider, components_description=None, protocol=PROTOCOL.FATE_FLOW):
        if not components_description:
            components_description = {}
        provider_info = ProviderInfo()
        provider_info.f_provider_name = provider.provider_name
        provider_info.f_name = provider.name
        provider_info.f_device = provider.device
        provider_info.f_version = provider.version
        provider_info.f_metadata = provider.metadata.dict()
        operator_type = cls.safe_save(ProviderInfo, defaults=provider_info.to_dict(),
                                      f_provider_name=provider.provider_name)
        cls.register_component(provider, components_description, protocol)
        return operator_type

    @classmethod
    def register_component(cls, provider: ComponentProvider, components_description, protocol):
        if not protocol:
            protocol = PROTOCOL.FATE_FLOW

        if not components_description:
            components_description = {}

        component_list = []

        if components_description:
            component_list = components_description.keys()
        else:
            entrypoint = cls.load_entrypoint(provider)
            if entrypoint:
                component_list = entrypoint.component_list
        for component_name in component_list:
            component = ComponentInfo()
            component.f_provider_name = provider.provider_name
            component.f_name = provider.name
            component.f_device = provider.device
            component.f_version = provider.version
            component.f_component_name = component_name
            component.f_protocol = protocol
            component.f_component_description = components_description.get(component_name)
            cls.safe_save(
                ComponentInfo, defaults=component.to_dict(),
                **dict(
                    f_provider_name=provider.provider_name,
                    f_name=provider.name,
                    f_device=provider.device,
                    f_version=provider.version,
                    f_component_name=component_name,
                    f_protocol=protocol
                )
            )

    @classmethod
    @filter_parameters()
    def query_provider(cls, **kwargs):
        return cls._query(ProviderInfo, **kwargs)

    @classmethod
    @filter_parameters()
    def delete_provider(cls, **kwargs):
        result = cls._delete(ProviderInfo, **kwargs)
        cls.delete_provider_component_info(**kwargs)
        return result

    @classmethod
    @filter_parameters()
    def delete_provider_component_info(cls, **kwargs):
        result = cls._delete(ComponentInfo, **kwargs)
        return result

    @classmethod
    def register_default_providers(cls):
        # register fate flow
        cls.register_provider(cls.get_fate_flow_provider())
        # try to register fate
        try:
            cls.register_provider(cls.get_default_fate_provider())
        except Exception as e:
            stat_logger.exception(e)

    @classmethod
    def get_all_components(cls):
        component_list = cls._query(ComponentInfo, force=True)
        return list(set([component.f_component_name for component in component_list]))

    @classmethod
    def get_flow_components(cls):
        component_list = cls._query(ComponentInfo, name="fate_flow", force=True)
        return list(set([component.f_component_name for component in component_list]))

    @classmethod
    @filter_parameters()
    def query_component_description(cls, **kwargs):
        descriptions = {}
        for info in cls._query(ComponentInfo, **kwargs):
            descriptions[info.f_component_name] = info.f_component_description
        return descriptions

    @classmethod
    def get_fate_flow_provider(cls):
        return cls.get_provider(
            name="fate_flow",
            version=get_flow_version(),
            device=ProviderDevice.LOCAL,
            metadata={
                "path": FATE_FLOW_PROVIDER_PATH,
                "venv": sys.executable
            })

    @classmethod
    def get_default_fate_provider(cls):
        return cls.get_provider(
            name="fate",
            version=get_default_fate_version(),
            device=ProviderDevice.LOCAL,
            metadata={
                "path": DEFAULT_FATE_PROVIDER_PATH,
                "venv": sys.executable
            })

    @classmethod
    def generate_provider_name(cls, name, version, device):
        return f"{name}:{version}@{device}"

    @classmethod
    def parser_provider_name(cls, provider_name):
        if not provider_name:
            return None, None, None
        try:
            return provider_name.split(":")[0], provider_name.split(":")[1].split("@")[0], provider_name.split(":")[1].split("@")[1]
        except:
            raise ValueError(f"Provider format should be name:version@device, please check: {provider_name}")

    @classmethod
    def check_provider_name(cls, provider_name):
        name, version, device = cls.parser_provider_name(provider_name)
        if not name or name == "*":
            name = DEFAULT_PROVIDER.get("name")
        if not version or version == "*":
            if not DEFAULT_PROVIDER.get("version"):
                DEFAULT_PROVIDER["version"] = get_versions().get(name.upper())
            version = DEFAULT_PROVIDER.get("version")
        if not device or device == "*":
            device = DEFAULT_PROVIDER.get("device")
        provider_info = cls.query_provider(name=name, version=version, device=device)
        if not provider_info:
            raise ValueError(f"Not found provider[{cls.generate_provider_name(name, version, device)}]")
        return cls.generate_provider_name(name, version, device)

    @staticmethod
    def load_entrypoint(provider) -> Union[None, EntrypointABC]:
        return FlowHub.load_provider_entrypoint(provider)
