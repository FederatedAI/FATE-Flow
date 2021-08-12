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

from fate_arch.common import log
from fate_flow.components._base import ComponentMeta

_flow_base = Path(__file__).resolve().parent.parent.parent

LOGGER = log.getLogger()


def _search_components(path):
    try:
        module_name = (
            path.absolute()
            .relative_to(_flow_base)
            .with_suffix("")
            .__str__()
            .replace("/", ".")
        )
        module = importlib.import_module(module_name)
    except ImportError as e:
        # or skip ?
        raise e
    _obj_pairs = inspect.getmembers(module, lambda obj: isinstance(obj, ComponentMeta))
    return _obj_pairs


class Components:
    @classmethod
    def get_names(cls) -> typing.Dict[str, dict]:
        names = {}
        _components_base = Path(__file__).resolve().parent
        for p in _components_base.glob("**/*.py"):
            for name, obj in _search_components(p):
                info = obj.register_info()
                LOGGER.info(f"component register {name} with cache info {info}")
                names.update(info)
        return names

    @classmethod
    def get(cls, name: str, cache) -> ComponentMeta:
        if cache:
            importlib.import_module(cache["module"])

        # temperary
        else:
            from .reader import reader_cpn_meta
            from .download import download_cpn_meta
            from .upload import upload_cpn_meta
            from .model_operation_components import (
                model_restore_cpn_meta,
                model_store_cpn_meta,
            )
        return ComponentMeta.get_meta(name)
