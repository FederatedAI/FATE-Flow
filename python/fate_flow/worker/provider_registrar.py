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
from fate_arch.common.base_utils import json_dumps
from fate_flow.utils.log_utils import getLogger
from fate_flow.db.component_registry import ComponentRegistry
from fate_flow.entity import ComponentProvider
from fate_flow.settings import stat_logger
from fate_flow.worker.base_worker import BaseWorker

LOGGER = getLogger()


class ProviderRegistrar(BaseWorker):
    def _run(self):
        provider = ComponentProvider(**self.args.config.get("provider"))
        support_components = ComponentRegistry.register_provider(provider)
        ComponentRegistry.register_components(provider, support_components)
        ComponentRegistry.dump()
        stat_logger.info(json_dumps(ComponentRegistry.REGISTRY, indent=4))


if __name__ == '__main__':
    ProviderRegistrar().run()
