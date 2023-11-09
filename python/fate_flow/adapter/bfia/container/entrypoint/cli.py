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
import json
import logging

import click

from fate_flow.adapter.bfia.container.wraps.wraps import BfiaWraps
from fate_flow.adapter.bfia.utils.spec.task import TaskRuntimeEnv

logger = logging.getLogger(__name__)


@click.group()
def component():
    """
    Manipulate components: execute, list, generate describe file
    """


@component.command()
def entrypoint():
    configs = load_config_from_env()
    logger = logging.getLogger(__name__)
    logger.debug(f"task config: {configs}")
    BfiaWraps(TaskRuntimeEnv(**configs)).run()


def load_config_from_env():
    import os

    config = {}
    component_env_keys = ["system", "config", "runtime"]
    sep = '.'

    for name in os.environ:
        for key in component_env_keys:
            if name.startswith(f"{key}{sep}"):
                conf = os.environ[name]
                try:
                    conf = json.loads(os.environ[name])
                except:
                    pass
                config[name] = conf

    return unflatten_dict(config)


def unflatten_dict(flat_dict, sep='.'):
    nested_dict = {}

    for key, value in flat_dict.items():
        keys = key.split(sep)
        temp_dict = nested_dict

        for k in keys[:-1]:
            if k not in temp_dict:
                temp_dict[k] = {}
            temp_dict = temp_dict[k]

        last_key = keys[-1]
        if last_key in temp_dict and not isinstance(temp_dict[last_key], dict):
            temp_dict[last_key] = {last_key: temp_dict[last_key]}
        if last_key in temp_dict:
            temp_dict[last_key].update({last_key: value})
        else:
            temp_dict[last_key] = value

    return nested_dict
