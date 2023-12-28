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
from typing import Union

from fate_flow.entity import BaseEntity
from fate_flow.entity.spec.flow import ProviderSpec, LocalProviderSpec, DockerProviderSpec, K8sProviderSpec


class ComponentProvider(BaseEntity):
    def __init__(self, provider_info: ProviderSpec):
        self._name = provider_info.name
        self._device = provider_info.device
        self._version = provider_info.version
        self._metadata = provider_info.metadata
        self._python_path = ""
        self._python_env = ""
        self.init_env()

    def init_env(self):
        if isinstance(self._metadata, LocalProviderSpec):
            self._python_path = self._metadata.path
            self._python_env = self._metadata.venv

    @property
    def name(self):
        return self._name

    @property
    def device(self):
        return self._device

    @property
    def version(self):
        return self._version

    @property
    def metadata(self) -> Union[LocalProviderSpec, DockerProviderSpec, K8sProviderSpec]:
        return self._metadata

    @property
    def python_path(self):
        return self._python_path

    @property
    def python_env(self):
        return self._python_env

    @property
    def provider_name(self):
        return f"{self.name}:{self.version}@{self.device}"

    def __eq__(self, other):
        return self.name == other.name and self.version == other.version
