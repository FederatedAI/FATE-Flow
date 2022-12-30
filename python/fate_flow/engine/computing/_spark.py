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
import os

from fate_flow.db.db_models import Task
from fate_flow.engine.computing._base import EngineABC
from fate_flow.entity.run_status import TaskStatus
from fate_flow.entity.types import KillProcessRetCode, WorkerName
from fate_flow.manager.worker_manager import WorkerManager
from fate_flow.utils import job_utils, process_utils


class SparkEngine(EngineABC):
    def run(self, task: Task, run_parameters, run_parameters_path, config_dir, log_dir, cwd_dir, **kwargs):
        # todo: get spark home from server registry
        spark_home = None
        if not spark_home:
            try:
                import pyspark
                spark_home = pyspark.__path__[0]
            except ImportError as e:
                raise RuntimeError("can not import pyspark")
            except Exception as e:
                raise RuntimeError("can not import pyspark")
        # else:
        #     raise ValueError(f"spark home must be configured in conf/service_conf.yaml when run on cluster mode")

        # additional configs
        spark_submit_config = run_parameters.get("conf", {}).get("computing", {}).get("metadata", {}).get("spark_run", {})

        deploy_mode = spark_submit_config.get("deploy-mode", "client")
        if deploy_mode not in ["client"]:
            raise ValueError(f"deploy mode {deploy_mode} not supported")

        spark_submit_cmd = os.path.join(spark_home, "bin/spark-submit")
        executable = [spark_submit_cmd, f"--name={task.f_task_id}#{task.f_role}"]
        for k, v in spark_submit_config.items():
            if k != "conf":
                executable.append(f"--{k}={v}")
        if "conf" in spark_submit_config:
            for ck, cv in spark_submit_config["conf"].items():
                executable.append(f"--conf")
                executable.append(f"{ck}={cv}")
        extra_env = {}
        extra_env["SPARK_HOME"] = spark_home
        return WorkerManager.start_task_worker(worker_name=WorkerName.TASK_EXECUTOR, task=task,
                                               task_parameters=run_parameters, executable=executable,
                                               extra_env=extra_env)

    def kill(self, task):
        kill_status_code = process_utils.kill_task_executor_process(task)
        # session stop
        if kill_status_code is KillProcessRetCode.KILLED or task.f_status not in {TaskStatus.WAITING}:
            job_utils.start_session_stop(task)

    def is_alive(self, task):
        return process_utils.check_process(pid=int(task.f_run_pid), task=task)
