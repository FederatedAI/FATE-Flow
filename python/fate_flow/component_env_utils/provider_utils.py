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
import pathlib

from fate_arch.common import file_utils
from fate_flow.entity import ComponentProvider


def get_provider_interface(provider: ComponentProvider):
    obj = get_component_class(provider, "interface")
    setattr(obj, "provider_name", provider.name)
    setattr(obj, "provider_version", provider.version)
    return obj


def get_component_model(provider: ComponentProvider):
    class_path = get_component_class_path(provider, "model")
    return pathlib.Path(file_utils.get_python_base_directory(*class_path)), class_path


def get_component_class(provider: ComponentProvider, class_name):
    class_path = get_component_class_path(provider, class_name)
    return getattr(importlib.import_module(".".join(class_path[:-1])), class_path[-1])


def get_component_class_path(provider: ComponentProvider, class_name):
    return f"{pathlib.Path(provider.path).name}.{provider.class_path.get(class_name)}".split(".")
