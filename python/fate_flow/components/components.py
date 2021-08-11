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

import typing
from ._base import ComponentMeta
import importlib


class Components:
    @classmethod
    def get_names(cls) -> typing.Dict[str, dict]:
        from .download import download_cpn_meta
        from .model_operation_components import (
            model_store_cpn_meta,
            model_restore_cpn_meta,
        )
        from .reader import reader_cpn_meta
        from .upload import upload_cpn_meta

        names = {}
        names.update(download_cpn_meta.register_info())
        names.update(model_store_cpn_meta.register_info())
        names.update(model_restore_cpn_meta.register_info())
        names.update(reader_cpn_meta.register_info())
        names.update(upload_cpn_meta.register_info())

        return names

    @classmethod
    def get(cls, name: str, cache) -> ComponentMeta:
        if cache:
            importlib.import_module(cache["module"])

        # temperary
        else:
            from .download import download_cpn_meta
            from .model_operation_components import (
                model_store_cpn_meta,
                model_restore_cpn_meta,
            )
            from .reader import reader_cpn_meta
            from .upload import upload_cpn_meta
        return ComponentMeta.get_meta(name)
