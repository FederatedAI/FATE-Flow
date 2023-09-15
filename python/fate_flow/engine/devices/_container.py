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
import yaml

from fate_flow.db.db_models import Task
from fate_flow.engine.devices._base import EngineABC
from fate_flow.entity.types import ProviderDevice
from fate_flow.runtime.runtime_config import RuntimeConfig
from fate_flow.utils.log_utils import schedule_logger


class ContainerdEngine(EngineABC):
    def __init__(self, provider):
        if provider.device == ProviderDevice.DOCKER:
            from fate_flow.manager.container.docker_manager import DockerManager
            self.manager = DockerManager(provider)
        elif provider.device == ProviderDevice.K8S:
            from fate_flow.manager.container.k8s_manager import K8sManager
            self.manager = K8sManager(provider)
        else:
            raise ValueError(f'worker "{provider.device}" is not supported')

    @staticmethod
    def _get_name(task: Task):
        return f'{task.f_role}-{task.f_party_id}-{task.f_task_id}-{task.f_task_version}'

    @staticmethod
    def _get_command(task: Task):
        return [
            '-m',
            'fate.components',
            'component',
            'execute',
            '--process-tag',
            task.f_execution_id,
            '--env-name',
            'FATE_TASK_CONFIG',
        ]

    @staticmethod
    def _get_environment(task: Task, run_parameters):
        return {
            'FATE_JOB_ID': task.f_job_id,
            'FATE_TASK_CONFIG': yaml.dump(run_parameters),
        }

    def run(self, task: Task, run_parameters, run_parameters_path, config_dir, log_dir, cwd_dir, **kwargs):
        name = self._get_name(task)
        cmd = self._get_command(task)
        env = self._get_environment(task, run_parameters)
        schedule_logger(job_id=task.f_job_id).info(f"start run container {name}, cmd: {cmd}, env: {env}")
        self.manager.start(name, cmd, env)
        return {
            'run_ip': RuntimeConfig.JOB_SERVER_HOST,
            'cmd': cmd
        }

    def kill(self, task: Task):
        self.manager.stop(self._get_name(task))

    def is_alive(self, task: Task):
        return self.manager.is_running(self._get_name(task))

    def cleanup(self, task: Task):
        pass

