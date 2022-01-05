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

from fate_flow.entity import ComponentProvider
from fate_flow.utils.log_utils import getLogger

LOGGER = getLogger()


def get_provider_interface(provider: ComponentProvider):
    obj = get_provider_class_object(provider, "interface")
    for i in ('name', 'version', 'path'):
        setattr(obj, f'provider_{i}', getattr(provider, i))
    return obj


def get_provider_model_paths(provider: ComponentProvider):
    model_import_path = get_provider_class_import_path(provider, "model")
    model_module_dir = pathlib.Path(provider.path).joinpath(*model_import_path[1:])
    return model_module_dir, model_import_path


def get_provider_class_object(provider: ComponentProvider, class_name, module=False):
    class_path = get_provider_class_import_path(provider, class_name)
    if module:
        return importlib.import_module(".".join(class_path))
    else:
        return getattr(importlib.import_module(".".join(class_path[:-1])), class_path[-1])


def get_provider_class_import_path(provider: ComponentProvider, class_name):
    return f"{pathlib.Path(provider.path).name}.{provider.class_path.get(class_name)}".split(".")
