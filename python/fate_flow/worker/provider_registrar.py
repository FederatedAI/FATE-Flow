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
import os
import sys
import traceback
import argparse
from fate_arch.common.base_utils import current_timestamp, json_dumps
from fate_arch.common.file_utils import load_json_conf
from fate_arch.common.log import getLogger
from fate_flow.entity.types import ProcessRole
from fate_flow.entity.component_provider import ComponentProvider
from fate_flow.db.runtime_config import RuntimeConfig
from fate_flow.settings import stat_logger
from fate_flow.db.component_registry import ComponentRegistry

LOGGER = getLogger()


class ProviderRegistrar(object):
    @classmethod
    def run(cls):
        stat_logger.info(f'enter {cls.__name__} process')
        stat_logger.info("python env: {}, python path: {}".format(os.getenv("VIRTUAL_ENV"), os.getenv("PYTHONPATH")))
        start_time = current_timestamp()
        try:
            parser = argparse.ArgumentParser()
            parser.add_argument("-c", "--config", required=True, type=str, help="provider config")
            args = parser.parse_args()
            RuntimeConfig.set_process_role(ProcessRole.EXECUTOR)
            config = load_json_conf(args.config)
            ComponentRegistry.load()
            provider = ComponentProvider(**config.get("provider"))
            support_components = ComponentRegistry.register_provider(provider)
            ComponentRegistry.register_components(provider, support_components)
            ComponentRegistry.dump()
            stat_logger.info(json_dumps(ComponentRegistry.REGISTRY, indent=4))
            sys.exit(0)
        except Exception as e:
            traceback.print_exc()
            stat_logger.exception(e)
            sys.exit(1)
        finally:
            end_time = current_timestamp()
            stat_logger.info(f'exit {cls.__name__} process, use {end_time - start_time} ms')


if __name__ == '__main__':
    ProviderRegistrar.run()
