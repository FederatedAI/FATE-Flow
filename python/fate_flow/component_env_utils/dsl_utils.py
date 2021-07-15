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
import importlib
from fate_flow.entity.types import ComponentProvider
from fate_flow.runtime_config import RuntimeConfig
from fate_flow.utils import job_utils


def get_component_framework_interface(component_provider: ComponentProvider, component_version):
    return get_component_class_path(component_provider, component_version, "framework_interface")


def get_component_class_path(component_provider: ComponentProvider, component_version, class_name):
    component_path = job_utils.get_component_path(component_provider, component_version)
    class_path = RuntimeConfig.COMPONENT_REGISTRY["provider"].get(component_provider, {}).get(component_version, {}).get("class_path", {}).get(class_name, None)
    if not class_path:
        class_path = RuntimeConfig.COMPONENT_REGISTRY["default_settings"]["class_path"][class_name]
    return importlib.import_module("{}.{}".format(".".join(component_path), class_path))