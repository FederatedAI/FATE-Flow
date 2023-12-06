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
import logging
import os
import sys
import typing

import yaml

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
    def get_component_define(cls, provider_name, task_info, stage):
        task_dir = get_task_directory(**task_info, output=True)
        component_ref = task_info.get("component")
        role = task_info.get("role")
        os.makedirs(task_dir, exist_ok=True)
        define_file = os.path.join(task_dir, "define.yaml")
        cmd = cls.generate_component_define_cmd(provider_name, component_ref, role, stage, define_file)
        logging.debug(f"load define cmd: {cmd}")
        if cmd:
            WorkerManager.start_task_worker(
                worker_name=WorkerName.COMPONENT_DEFINE,
                task_info=task_info,
                common_cmd=cmd,
                sync=True
            )
            if os.path.exists(define_file):
                with open(define_file, "r") as fr:
                    return yaml.safe_load(fr)
        return {}

    def _cleanup1(self, **kwargs):
        # backend cleanup
        pass

    def _cleanup2(self, provider_name, task_info, config, **kwargs):
        # engine cleanup: computing、federation ..
        cmd = self.generate_cleanup_cmd(provider_name)

        if cmd:
            logging.info(f"start clean task, config: {config}")
            WorkerManager.start_task_worker(
                worker_name=WorkerName.TASK_EXECUTE_CLEAN,
                task_info=task_info,
                common_cmd=cmd,
                task_parameters=config,
                sync=True
            )
            logging.info(f"clean success")

    def cleanup(self, provider_name, task_info, config, party_task_id, **kwargs):
        self._cleanup1(session_id=party_task_id, task_info=task_info)
        self._cleanup2(provider_name, task_info, config, **kwargs)

    @staticmethod
    def generate_component_run_cmd(provider_name, conf_path, output_path=""):
        if provider_name == ProviderName.FATE:
            from fate_flow.manager.worker.fate_executor import FateSubmit
            module_file_path = sys.modules[FateSubmit.__module__].__file__

        elif provider_name == ProviderName.FATE_FLOW:
            from fate_flow.manager.worker.fate_flow_executor import FateFlowSubmit
            module_file_path = sys.modules[FateFlowSubmit.__module__].__file__

        else:
            raise ValueError(f"load provider {provider_name} failed")
        os.environ.pop("FATE_TASK_CONFIG", None)
        common_cmd = [
            module_file_path,
            "component",
            "execute",
            "--config",
            conf_path,
            "--execution-final-meta-path",
            output_path
        ]

        return common_cmd

    @staticmethod
    def generate_component_define_cmd(provider_name, component_ref, role, stage, define_file):
        cmd = []
        if provider_name == ProviderName.FATE:
            from fate_flow.manager.worker.fate_executor import FateSubmit
            module_file_path = sys.modules[FateSubmit.__module__].__file__
            cmd = [
                module_file_path,
                "component",
                "artifact-type",
                "--name",
                component_ref,
                "--role",
                role,
                "--stage",
                stage,
                "--output-path",
                define_file
            ]
        return cmd

    @staticmethod
    def generate_cleanup_cmd(provider_name):
        cmd = []
        if provider_name == ProviderName.FATE:
            from fate_flow.manager.worker.fate_executor import FateSubmit
            module_file_path = sys.modules[FateSubmit.__module__].__file__
            cmd = [
                module_file_path,
                "component",
                "cleanup",
                "--env-name",
                "FATE_TASK_CONFIG",
            ]
        return cmd
