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
from ruamel import yaml

from fate_flow.db.db_models import Task
from fate_flow.settings import LOCAL_DATA_STORE_PATH, LOG_DIRECTORY, WORKER


class ContainerdWorkerManager:
    worker_type = WORKER.get('type', '')

    def __init__(self):
        if self.worker_type == 'docker':
            from fate_flow.manager.docker_manager import DockerManager
            self.manager = DockerManager()
        elif self.worker_type == 'k8s':
            from fate_flow.manager.k8s_manager import K8sManager
            self.manager = K8sManager()
        else:
            raise ValueError(f'worker "{self.worker_type}" is not supported')

    def get_name(self, task: Task):
        return f'{task.f_role}-{task.f_party_id}-{task.f_task_id}-{task.f_task_version}'

    def get_command(self, task: Task):
        return [
            '-m',
            "fate.components"
            'component',
            'execute',
            '--process-tag',
            task.f_execution_id,
            '--env-name',
            'FATE_TASK_CONFIG',
        ]

    def get_environment(self, task: Task, run_parameters):
        return {
            'FATE_JOB_ID': task.f_job_id,
            'FATE_TASK_CONFIG': yaml.dump(run_parameters),
            'STANDALONE_DATA_PATH': f'{LOCAL_DATA_STORE_PATH}/__standalone_data__',
        }

    def run(self, task: Task, run_parameters, run_parameters_path, config_dir, log_dir, cwd_dir, **kwargs):
        self.manager.start(
            self.get_name(task),
            self.get_command(task),
            self.get_environment(task, run_parameters),
            volumes=[
                f'{LOCAL_DATA_STORE_PATH}:{LOCAL_DATA_STORE_PATH}',
                f'{LOG_DIRECTORY}:{LOG_DIRECTORY}',
            ],
        )
        return {}

    def kill(self, task):
        self.manager.stop(self.get_name(task))

    def is_alive(self, task):
        return self.manager.is_running(self.get_name(task))
