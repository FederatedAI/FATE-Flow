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
import sys

from fate_flow.hub.provider import EntrypointABC


class LocalFateEntrypoint(EntrypointABC):
    def __init__(self, provider):
        self.provider = provider

    @property
    def component_list(self):
        if self.provider.python_path and self.provider.python_path not in sys.path:
            sys.path.append(self.provider.python_path)
        from fate.components.core import list_components
        # {'buildin': [], 'thirdparty': []}
        components = list_components()
        _list = components.get('buildin', [])
        _list.extend(components.get("thirdparty", []))
        return _list

    @property
    def component_description(self):
        return {}


class FATEFLowEntrypoint(EntrypointABC):
    def __init__(self, provider):
        self.provider = provider

    @property
    def component_list(self):
        from fate_flow.components.components import BUILDIN_COMPONENTS
        return [component.name for component in BUILDIN_COMPONENTS]

    @property
    def component_description(self):
        return {}
