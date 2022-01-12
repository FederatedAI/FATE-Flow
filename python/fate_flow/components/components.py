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
import inspect
import typing
from pathlib import Path

from fate_flow.utils.log_utils import getLogger
from fate_flow.components._base import ComponentMeta


LOGGER = getLogger()


def _get_module_name_by_path(path, base):
    return '.'.join(path.resolve().relative_to(base.resolve()).with_suffix('').parts)


def _search_components(path, base):
    try:
        module_name = _get_module_name_by_path(path, base)
        module = importlib.import_module(module_name)
    except ImportError as e:
        # or skip ?
        raise e
    _obj_pairs = inspect.getmembers(module, lambda obj: isinstance(obj, ComponentMeta))
    return _obj_pairs, module_name


class Components:
    provider_version = None
    provider_name = None
    provider_path = None

    @classmethod
    def _module_base(cls):
        return Path(cls.provider_path).resolve().parent

    @classmethod
    def _components_base(cls):
        return Path(cls.provider_path, 'components').resolve()

    @classmethod
    def get_names(cls) -> typing.Dict[str, dict]:
        names = {}
        for p in cls._components_base().glob("**/*.py"):
            obj_pairs, module_name = _search_components(p.resolve(), cls._module_base())
            for name, obj in obj_pairs:
                names[obj.name] = {"module": module_name}
                LOGGER.info(f"component register {obj.name} with cache info {module_name}")
        return names

    @classmethod
    def get(cls, name: str, cache) -> ComponentMeta:
        if cache:
            importlib.import_module(cache[name]["module"])
        else:
            for p in cls._components_base().glob("**/*.py"):
                module_name = _get_module_name_by_path(p, cls._module_base())
                importlib.import_module(module_name)

        cpn = ComponentMeta.get_meta(name)
        return cpn
