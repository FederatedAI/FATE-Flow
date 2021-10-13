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

from fate_flow.controller.engine_controller.engine import EngineABC
from fate_flow.db.db_models import Task
from fate_flow.entity.run_status import TaskStatus
from fate_flow.entity.types import KillProcessRetCode, WorkerName
from fate_flow.manager.worker_manager import WorkerManager
from fate_flow.utils import job_utils, process_utils


class EggrollEngine(EngineABC):
    def run(self, task: Task, run_parameters, run_parameters_path, config_dir, log_dir, cwd_dir, **kwargs):
        return WorkerManager.start_task_worker(worker_name=WorkerName.TASK_EXECUTOR, task=task,
                                               task_parameters=run_parameters)

    def kill(self, task):
        kill_status_code = process_utils.kill_task_executor_process(task)
        # session stop
        if kill_status_code is KillProcessRetCode.KILLED or task.f_status not in {TaskStatus.WAITING}:
            job_utils.start_session_stop(task)

    def is_alive(self, task):
        return process_utils.check_process(pid=int(task.f_run_pid), task=task)
