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
from fate_arch.common.base_utils import current_timestamp, json_dumps
from fate_arch.common.log import getLogger
from fate_flow.entity.types import ProcessRole
from fate_flow.db.runtime_config import RuntimeConfig
from fate_flow.settings import stat_logger

LOGGER = getLogger()


class ComponentRegistryInitializer(object):
    @classmethod
    def run(cls):
        try:
            stat_logger.info('enter component registry initializer process')
            stat_logger.info("python env: {}, python path: {}".format(os.getenv("VIRTUAL_ENV"), os.getenv("PYTHONPATH")))
            # init function args
            RuntimeConfig.set_process_role(ProcessRole.EXECUTOR)
            start_time = current_timestamp()
            RuntimeConfig.load_component_registry()
            RuntimeConfig.register_default_providers()
            RuntimeConfig.dump_component_registry()
            RuntimeConfig.load_component_registry()
            stat_logger.info(json_dumps(RuntimeConfig.COMPONENT_REGISTRY, indent=4))
            end_time = current_timestamp()
            elapsed = end_time - start_time
        except Exception as e:
            traceback.print_exc()
            stat_logger.exception(e)
            sys.exit(1)


if __name__ == '__main__':
    ComponentRegistryInitializer.run()
