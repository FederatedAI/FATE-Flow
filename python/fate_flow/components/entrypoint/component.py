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

from fate_flow.entity.spec.dag import TaskConfigSpec

logger = logging.getLogger(__name__)


def execute_component(config: TaskConfigSpec):
    component = load_component(config.component)
    cpn_config = config.parameters
    cpn_config["job_id"] = config.job_id
    logger.info(f"cpn_config： {cpn_config}")

    component.execute(cpn_config)


def load_component(cpn_name: str):
    from fate_flow.components.components import BUILDIN_COMPONENTS

    for cpn in BUILDIN_COMPONENTS:
        if cpn.name == cpn_name:
            return cpn
