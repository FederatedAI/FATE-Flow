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
from fate_flow.engine.backend._base import LocalEngine
from fate_flow.entity.types import WorkerName
from fate_flow.manager.service.worker_manager import WorkerManager


class EggrollEngine(LocalEngine):
    def run(self, task_info, run_parameters, provider_name, output_path):
        return WorkerManager.start_task_worker(
            worker_name=WorkerName.TASK_EXECUTE,
            task_info=task_info,
            common_cmd=self.generate_component_run_cmd(provider_name, output_path),
            task_parameters=run_parameters
        )

