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
from functools import wraps
import flask
from fate_flow.entity import RetCode
from fate_flow.utils.api_utils import get_json_result


def check_config(config: typing.Dict, required_arguments: typing.List):
    if not config or not isinstance(config, dict):
        raise TypeError('no parameters')

    no_arguments = []
    error_arguments = []
    for require_argument in required_arguments:
        if isinstance(require_argument, tuple):
            config_value = config.get(require_argument[0], None)
            if isinstance(require_argument[1], (tuple, list)):
                if config_value not in require_argument[1]:
                    error_arguments.append(require_argument)
            elif config_value != require_argument[1]:
                error_arguments.append(require_argument)
        elif require_argument not in config:
            no_arguments.append(require_argument)

    if no_arguments or error_arguments:
        error_string = ""
        if no_arguments:
            error_string += "required parameters are missing: {}; ".format(",".join(no_arguments))
        if error_arguments:
            error_string += "required parameter values: {}".format(",".join(["{}={}".format(a[0], a[1]) for a in error_arguments]))
        raise KeyError(error_string)


def validate_request(*args, **kwargs):
    def wrapper(func):
        @wraps(func)
        def decorated_function(*_args, **_kwargs):
            input_arguments = flask.request.json or flask.request.form.to_dict()
            no_arguments = []
            error_arguments = []
            for arg in args:
                if arg not in input_arguments:
                    no_arguments.append(arg)
            for k, v in kwargs.items():
                config_value = input_arguments.get(k, None)
                if config_value is None:
                    no_arguments.append(k)
                elif isinstance(v, (tuple, list)):
                    if config_value not in v:
                        error_arguments.append((k, set(v)))
                elif config_value != v:
                    error_arguments.append((k, v))
            if no_arguments or error_arguments:
                error_string = ""
                if no_arguments:
                    error_string += "required argument are missing: {}; ".format(",".join(no_arguments))
                if error_arguments:
                    error_string += "required argument values: {}".format(",".join(["{}={}".format(a[0], a[1]) for a in error_arguments]))
                return get_json_result(retcode=RetCode.ARGUMENT_ERROR, retmsg=error_string)
            return func(*_args, **_kwargs)
        return decorated_function
    return wrapper