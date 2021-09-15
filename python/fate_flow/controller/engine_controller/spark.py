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
import sys

from fate_arch.common.log import schedule_logger
from fate_flow.controller.engine_controller.engine import EngineABC
from fate_flow.db.runtime_config import RuntimeConfig
from fate_flow.entity.component_provider import ComponentProvider
from fate_flow.entity.types import KillProcessRetCode
from fate_flow.entity.run_status import TaskStatus
from fate_flow.manager.dependence_manager import DependenceManager
from fate_flow.worker.task_executor import TaskExecutor
from fate_flow.utils import job_utils, process_utils
from fate_flow.db.db_models import Task


class SparkEngine(EngineABC):
    def run(self, task: Task, run_parameters, run_parameters_path, config_dir, log_dir, cwd_dir, **kwargs):
        if "SPARK_HOME" not in os.environ:
            raise EnvironmentError("SPARK_HOME not found")
        spark_home = os.environ["SPARK_HOME"]

        # additional configs
        spark_submit_config = run_parameters.spark_run

        deploy_mode = spark_submit_config.get("deploy-mode", "client")
        if deploy_mode not in ["client"]:
            raise ValueError(f"deploy mode {deploy_mode} not supported")

        spark_submit_cmd = os.path.join(spark_home, "bin/spark-submit")
        process_cmd = [spark_submit_cmd, f"--name={task.f_task_id}#{task.f_role}"]
        for k, v in spark_submit_config.items():
            if k != "conf":
                process_cmd.append(f"--{k}={v}")
        if "conf" in spark_submit_config:
            for ck, cv in spark_submit_config["conf"].items():
                process_cmd.append(f"--conf")
                process_cmd.append(f"{ck}={cv}")
        provider = ComponentProvider(**task.f_provider_info)
        schedule_logger(task.f_job_id).info(f"provider env:{provider.env}")
        extra_env = provider.env
        dependence = DependenceManager(task.f_provider_info, job_id=task.f_job_id)
        executor_env_pythonpath = dependence.get_executor_env_pythonpath()
        executor_env_python = dependence.get_executor_python_env()
        driver_env_python = dependence.get_driver_python_env()
        archives = dependence.get_archives()
        schedule_logger(task.f_job_id).info(f"executor_env_python {process_cmd}，executor_env_python {executor_env_python}，"
                                            f"driver_env_python {driver_env_python}， archives {archives}")
        process_cmd.append(f'--archives')
        process_cmd.append(archives)
        process_cmd.append(f'--conf')
        process_cmd.append(f'spark.pyspark.python={executor_env_python}')
        process_cmd.append(f'--conf')
        process_cmd.append(f'spark.executorEnv.PYTHONPATH={executor_env_pythonpath}')
        process_cmd.append(f'--conf')
        process_cmd.append(f'spark.pyspark.driver.python={driver_env_python}')
        process_cmd.extend([
            sys.modules[TaskExecutor.__module__].__file__,
            "-j", task.f_job_id,
            "-n", task.f_component_name,
            "-t", task.f_task_id,
            "-v", task.f_task_version,
            "-r", task.f_role,
            "-p", task.f_party_id,
            "-c", run_parameters_path,
            "--run_ip", RuntimeConfig.JOB_SERVER_HOST,
            "--job_server", f"{RuntimeConfig.JOB_SERVER_HOST}:{RuntimeConfig.HTTP_PORT}",
        ])
        schedule_logger(task.f_job_id).info(f"process cmd {process_cmd}")
        schedule_logger(task.f_job_id).info(f"task {task.f_task_id} {task.f_task_version} on {task.f_role} {task.f_party_id} executor subprocess is ready")
        p = process_utils.run_subprocess(job_id=task.f_job_id, config_dir=config_dir, process_cmd=process_cmd, log_dir=log_dir,
                                     cwd_dir=cwd_dir,extra_env=extra_env)
        return {"run_pid": p.pid}

    def kill(self, task):
        kill_status_code = process_utils.kill_task_executor_process(task)
        # session stop
        if kill_status_code == KillProcessRetCode.KILLED or task.f_status not in {TaskStatus.WAITING}:
            job_utils.start_session_stop(task)

    def is_alive(self, task):
        return process_utils.check_job_process(pid=int(task.f_run_pid), task=task)
