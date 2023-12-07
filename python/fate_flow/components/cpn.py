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
import inspect
import logging
from typing import Any

from pydantic import BaseModel


class Params(BaseModel):
    class TaskParams(BaseModel):
        job_id: str

    component_params: Any
    task_params: TaskParams


class _Component:
    def __init__(
        self,
        name: str,
        callback
    ) -> None:
        self.name = name
        self.callback = callback

    def execute(self, config, outputs):
        return self.callback(config, outputs)


def component(*args, **kwargs):
    def decorator(f):
        cpn_name = f.__name__.lower()
        if isinstance(f, _Component):
            raise TypeError("Attempted to convert a callback into a component twice.")
        cpn = _Component(
            name=cpn_name,
            callback=f
        )
        cpn.__doc__ = f.__doc__
        # cpn.validate_declare()
        return cpn
    return decorator
