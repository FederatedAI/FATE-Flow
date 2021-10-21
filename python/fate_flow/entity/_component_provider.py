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

from fate_flow.entity.types import ComponentProviderName
from fate_flow.entity import BaseEntity


class ComponentProvider(BaseEntity):
    def __init__(self, name: str, version: str, path: str, class_path: dict, **kwargs):
        if not ComponentProviderName.valid(name):
            raise ValueError(f"not support {name} provider")
        self._name = name
        self._version = version
        self._path = path
        self._class_path = class_path
        self._env = {}
        self.init_env()

    def init_env(self):
        self._env["PYTHONPATH"] = os.path.join("/", *self._path.split("/")[:-1])

    @property
    def name(self):
        return self._name

    @property
    def version(self):
        return self._version

    @property
    def path(self):
        return self._path

    @property
    def class_path(self):
        return self._class_path

    @property
    def env(self):
        return self._env

    def __eq__(self, other):
        return self.name == other.name and self.version == other.version
