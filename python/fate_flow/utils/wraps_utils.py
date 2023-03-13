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
from functools import wraps

from fate_flow.entity.code import ReturnCode


def filter_parameters(filter_value=None):
    def _inner(func):
        @wraps(func)
        def _wrapper(*args, **kwargs):
            _kwargs = {}
            for k, v in kwargs.items():
                if v != filter_value:
                    _kwargs[k] = v
            return func(*args, **_kwargs)
        return _wrapper
    return _inner


def switch_function(switch, code=ReturnCode.Server.FUNCTION_RESTRICTED, message="function restricted"):
    def _inner(func):
        @wraps(func)
        def _wrapper(*args, **kwargs):
            if switch:
                return func(*args, **kwargs)
            else:
                raise Exception(code, message)
        return _wrapper
    return _inner
