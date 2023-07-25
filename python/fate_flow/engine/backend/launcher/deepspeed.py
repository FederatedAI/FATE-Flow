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
import datetime
import os
import sys
from abc import ABC

from fate_flow.engine.backend._base import EngineABC
from fate_flow.entity.types import BaseStatus


class StatusSet(BaseStatus):
    NEW = "NEW"
    NEW_TIMEOUT = "NEW_TIMEOUT"
    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"
    KILLED = "KILLED"
    ERROR = "ERROR"
    FINISHED = "FINISHED"


class EndStatus(BaseStatus):
    NEW_TIMEOUT = StatusSet.NEW_TIMEOUT
    CLOSED = StatusSet.CLOSED
    FAILED = StatusSet.KILLED
    ERROR = StatusSet.ERROR
    FINISHED = StatusSet.FINISHED


class EggrollDeepspeedEngine(EngineABC, ABC):
    @staticmethod
    def run(self, task_info, run_parameters, engine_run, provider_name, output_path):
        parameters = TaskConfigSpec.parse_obj(run_parameters)
        if parameters.conf.computing.type == ComputingEngine.EGGROLL:
            # update eggroll options
            parameters.conf.computing.metadata.options.update(engine_run)
        return WorkerManager.start_task_worker(
            worker_name=WorkerName.TASK_EXECUTE,
            task_info=task_info,
            common_cmd=self.generate_component_run_cmd(provider_name, output_path),
            task_parameters=parameters.dict()
        )