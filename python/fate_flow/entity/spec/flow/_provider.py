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
import os
from typing import Optional, Union

import pydantic

from fate_flow.errors.server_error import FileNoFound


class BaseProvider(pydantic.BaseModel):
    def __init__(self, check=False, **kwargs):
        super(BaseProvider, self).__init__(**kwargs)
        if check:
            self.check()

    def check(self):
        pass


class LocalProviderSpec(BaseProvider):
    def check(self):
        if not os.path.exists(self.path):
            raise FileNoFound(path=self.path)
        if self.venv and not os.path.exists(self.venv):
            raise FileNoFound(venv=self.venv)

    path: str
    venv: Optional[str]


class DockerProviderSpec(BaseProvider):
    base_url: str
    image: str


class K8sProviderSpec(BaseProvider):
    image: str
    namespace: str
    config: Optional[dict]


class ProviderSpec(BaseProvider):
    name: str
    version: str
    device: str
    metadata: Union[LocalProviderSpec, DockerProviderSpec, K8sProviderSpec]
