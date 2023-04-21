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

from fate_flow.db import ProviderInfo
from fate_flow.db.base_models import DB, BaseModelOperate
from fate_flow.entity.spec import ProviderSpec, LocalProviderSpec, DockerProviderSpec, K8sProviderSpec
from fate_flow.runtime.system_settings import DEFAULT_FATE_PROVIDER_PATH, DEFAULT_PROVIDER
from fate_flow.runtime.component_provider import ComponentProvider, ProviderDevice
from fate_flow.utils.file_utils import get_fate_flow_directory
from fate_flow.utils.version import get_versions
from fate_flow.utils.wraps_utils import filter_parameters


class ProviderManager(BaseModelOperate):
    @classmethod
    def get_provider_by_provider_name(cls, provider_name) -> ComponentProvider:
        name, version, device = cls.parser_provider_name(provider_name)
        provider_list = [provider_info for provider_info in cls.query_provider(name=name, versin=version, device=device)]
        if not provider_list:
            raise ValueError(f"Query provider info failed: {provider_name}")
        provider_info = provider_list[0]
        return cls.get_provider(provider_info.f_name, provider_info.f_device, provider_info.f_version,
                                provider_info.f_metadata)

    @classmethod
    def get_provider(cls, name, device, version, metadata) -> Union[ComponentProvider, None]:
        if device == ProviderDevice.LOCAL:
            metadata = LocalProviderSpec(**metadata)
        elif type == ProviderDevice.DOCKER:
            metadata = DockerProviderSpec(**metadata)
        elif type == ProviderDevice.K8S:
            metadata = K8sProviderSpec(**metadata)
        else:
            return None
        return ComponentProvider(ProviderSpec(name=name, device=device, version=version, metadata=metadata))

    @classmethod
    @DB.connection_context()
    def register_provider(cls, provider: ComponentProvider):
        provider_info = ProviderInfo()
        provider_info.f_provider_name = cls.generate_provider_name(name=provider.name, version=provider.version,
                                                                   device=provider.device)
        provider_info.f_name = provider.name
        provider_info.f_device = provider.device
        provider_info.f_version = provider.version
        provider_info.f_metadata = provider.metadata.dict()
        operator_type = cls.safe_save(ProviderInfo, defaults=provider_info.to_dict(),
                                      f_provider_name=cls.generate_provider_name(provider.name, provider.version,
                                                                                 provider.device))
        # todo: load entrypoint、components、params...
        return operator_type

    @classmethod
    @filter_parameters()
    def query_provider(cls, **kwargs):
        return cls._query(ProviderInfo, **kwargs)

    @classmethod
    @filter_parameters()
    def delete_provider(cls, **kwargs):
        result = cls._delete(ProviderInfo, **kwargs)
        return result

    @classmethod
    def register_default_providers(cls):
        # register fate flow
        cls.register_provider(cls.get_fate_flow_provider())
        # register fate
        cls.register_provider(cls.get_default_fate_provider())

    @classmethod
    def get_fate_flow_provider(cls):
        return cls.get_provider(
            name="fate_flow",
            version=get_versions()["FATEFlow"],
            device=ProviderDevice.LOCAL,
            metadata={
                "path": get_fate_flow_directory("python"),
                "venv": sys.executable
            })

    @classmethod
    def get_default_fate_provider(cls):
        if not os.path.exists(DEFAULT_FATE_PROVIDER_PATH):
            raise Exception(f"default fate provider not exists: {DEFAULT_FATE_PROVIDER_PATH}")
        return cls.get_provider(
            name="fate",
            version=get_versions()["FATE"],
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