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
import sys

from fate_flow.component_env_utils.provider_utils import get_provider_class_object
from fate_flow.entity import ComponentProvider
from fate_flow.manager.provider_manager import ProviderManager


def get_python_path(provider_info):
    return provider_info.get("env").get("PYTHONPATH")


def get_fate_algorithm_path(provider_info):
    return provider_info.get("path")


def get_class_path(provider_info, name):
    return provider_info.get("class_path").get(name)


def import_path(path):
    sys.path.append(path)


def import_python_path(provider_info):
    import_path(get_python_path(provider_info))


def import_component_output_depend(provider_info=None):
    if not provider_info:
        provider_info = ProviderManager.get_default_fate_provider().to_dict()
    import_python_path(provider_info)


def get_class_object(class_name):
    provider_info = ProviderManager.get_default_fate_provider().to_dict()
    import_python_path(provider_info)
    provider = ComponentProvider(**provider_info)
    class_obj = get_provider_class_object(provider, class_name)
    return class_obj
