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
import re
from abc import ABC

from fate_flow.hub.provider import EntrypointABC
from fate_flow.manager.container.docker_manager import DockerManager


class DockerEntrypoint(EntrypointABC, ABC):
    def __init__(self, provider):
        self.provider = provider
        self.manager = DockerManager(provider)

    @property
    def component_list(self):
        return self.component_dict.keys()

    @property
    def component_dict(self):
        labels = self.manager.get_labels()
        _dict = {}
        pattern = r'^component\.\d*\.name$'
        for key, cpn_name in labels.items():
            if re.match(pattern, key):
                _k = key.rstrip(".name")
                _dict[key] = cpn_name
        return _dict

    @property
    def component_description(self):
        return {}
