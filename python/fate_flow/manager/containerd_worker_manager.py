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
from fate_flow.db.db_models import Task
from fate_flow.manager.docker_manager import DockerManager
from fate_flow.manager.k8s_manager import K8sManager
from fate_flow.settings import WORKER
from fate_flow.utils.file_utils import get_fate_flow_directory
from fate_flow.utils.job_utils import get_task_directory


class ContainerdWorkerManager:
    worker_type = WORKER.get('type', '')
    fate_root = WORKER.get('fate_root', '')

    def __init__(self):
        if self.worker_type == 'docker':
            self.manager = DockerManager()
        elif self.worker_type == 'k8s':
            self.manager = K8sManager()
        else:
            raise ValueError(f'worker "{self.worker_type}" is not supported')

    def get_name(task: Task):
        return f'{Task.f_role}#{Task.f_party_id}#{Task.f_job_id}#{Task.f_task_id}#{Task.f_task_version}'

    def get_command(self, task: Task):
        config_dir = get_task_directory(
            task.f_job_id,
            task.f_role,
            task.f_party_id,
            task.f_task_name,
            task.f_task_id,
            task.f_task_version,
        )

        return [
            f'{self.fate_root}/fateflow/python/fate_flow/worker/executor.py',
            'component',
            'execute',
            '--process-tag',
            task.f_execution_id,
            '--config',
            f'{config_dir}/task_parameters.json',
        ]

    def get_environment(self, task: Task):
        return {
            'FATE_JOB_ID': task.f_job_id,
        }

    def get_volumes(self, task: Task):
        return [
            f'{get_fate_flow_directory("jobs")}:{self.fate_root}/fateflow/jobs',
            f'{get_fate_flow_directory("logs")}:{self.fate_root}/fateflow/logs',
        ]

    def run(self, task: Task, run_parameters, run_parameters_path, config_dir, log_dir, cwd_dir, **kwargs):
        return self.manager.start(
            self.get_name(task),
            self.get_command(task),
            self.get_environment(task),
            self.get_volumes(task),
        )

    def kill(self, task):
        return self.manager.stop(self._get_name(task))

    def is_alive(self, task):
        return self.manager.is_running(self._get_name(task))
