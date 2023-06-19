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
import json
import os
import sys
import typing

from fate_flow.db.db_models import Task
from fate_flow.entity.types import ProviderName, WorkerName
from fate_flow.manager.service.worker_manager import WorkerManager
from fate_flow.utils.job_utils import get_task_directory


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
    @classmethod
    def get_component_define(cls, provider_name, task_info):
        task_dir = get_task_directory(**task_info)
        os.makedirs(task_dir, exist_ok=True)
        define_file = os.path.join(task_dir, "define.json")
        cmd = cls.generate_component_define_cmd(provider_name, define_file)
        if cmd:
            p = WorkerManager.start_task_worker(
                worker_name=WorkerName.COMPONENT_DEFINE,
                task_info=task_info,
                common_cmd=cmd
            )
            p.wait()
        if os.path.exists(define_file):
            with open(define_file, "r") as fr:
                return json.load(fr)
        return {}

    @staticmethod
    def generate_component_run_cmd(provider_name, path=""):
        if provider_name == ProviderName.FATE:
            from fate_flow.worker.fate_executor import FateSubmit
            module_file_path = sys.modules[FateSubmit.__module__].__file__
            common_cmd = [
                module_file_path,
                "component",
                "execute",
                "--env-name",
                "FATE_TASK_CONFIG",
            ]

        elif provider_name == ProviderName.FATE_FLOW:
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
            raise ValueError(f"load provider {provider_name} failed")
        return common_cmd

    @staticmethod
    def generate_component_define_cmd(provider_name, define_file):
        cmd = []
        if provider_name == ProviderName.FATE_FLOW:
            from fate_flow.worker.fate_executor import FateSubmit
            module_file_path = sys.modules[FateSubmit.__module__].__file__
            cmd = [
                module_file_path,
                "component",
                "cleanup",
                "--path",
                define_file
            ]
            return None

        return cmd
