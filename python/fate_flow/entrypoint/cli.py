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
import logging

import click

from fate_flow.components.entrypoint.component import execute_component
from fate_flow.entity.spec import TaskConfigSpec
from fate_flow.hub.flow_hub import FlowHub


@click.group()
def component():
    """
    Manipulate components: execute, list, generate describe file
    """


@component.command()
@click.option("--config", required=False, type=click.File(), help="config path")
@click.option("--env-name", required=False, type=str, help="env name for config")
def entrypoint(config, env_name):
    # parse config
    configs = {}
    load_config_from_env(configs, env_name)
    load_config_from_file(configs, config)
    task_config = TaskConfigSpec.parse_obj(configs)
    task_config.conf.logger.install()
    logger = logging.getLogger(__name__)
    logger.debug("logger installed")
    logger.debug(f"task config: {task_config}")
    FlowHub.load_components_wraps(config=task_config).run()


@component.command()
@click.option("--config", required=False, type=click.File(), help="config path")
@click.option("--env-name", required=False, type=str, help="env name for config")
def execute(config, env_name):
    # parse config
    configs = {}
    load_config_from_env(configs, env_name)
    load_config_from_file(configs, config)
    task_config = TaskConfigSpec.parse_obj(configs)
    task_config.conf.logger.install()
    logger = logging.getLogger(__name__)
    logger.debug("logger installed")
    logger.debug(f"task config: {task_config}")
    execute_component(task_config)



def load_config_from_file(configs, config_file):
    from ruamel import yaml

    if config_file is not None:
        configs.update(yaml.safe_load(config_file))
    return configs


def load_config_from_env(configs, env_name):
    import os
    from ruamel import yaml

    if env_name is not None and os.environ.get(env_name):
        configs.update(yaml.safe_load(os.environ[env_name]))
    return configs
