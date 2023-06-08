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


import abc
import sys
import typing

from fate_flow.db.db_models import Task
from fate_flow.entity.types import ProviderName


class EngineABC(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def run(self, task: Task, run_parameters, run_parameters_path, config_dir, log_dir, cwd_dir, **kwargs) -> typing.Dict:
        ...

    @abc.abstractmethod
    def kill(self, task: Task):
        ...

    @abc.abstractmethod
    def is_alive(self, task: Task):
        ...


class LocalEngine(object):
    @staticmethod
    def generate_cmd(local_provider_name):

        if local_provider_name == ProviderName.FATE:
            from fate_flow.worker.fate_executor import FateSubmit
            module_file_path = sys.modules[FateSubmit.__module__].__file__
            common_cmd = [
                module_file_path,
                "component",
                "execute",
                "--env-name",
                "FATE_TASK_CONFIG",
            ]

        elif local_provider_name == ProviderName.FATE_FLOW:
            from fate_flow.worker.fate_flow_executor import FateFlowSubmit
            module_file_path = sys.modules[FateFlowSubmit.__module__].__file__
            common_cmd = [
                module_file_path,
                "component",
                "execute",
                "--env-name",
                "FATE_TASK_CONFIG",
            ]
        else:
            raise ValueError(f"load local provider {local_provider_name} failed")
        return common_cmd
