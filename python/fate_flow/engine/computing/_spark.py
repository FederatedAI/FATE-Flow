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
        process_cmd = [spark_submit_cmd, f"--name={task.f_task_id}#{task.f_role}"]
        for k, v in spark_submit_config.items():
            if k != "conf":
                process_cmd.append(f"--{k}={v}")
        if "conf" in spark_submit_config:
            for ck, cv in spark_submit_config["conf"].items():
                process_cmd.append(f"--conf")
                process_cmd.append(f"{ck}={cv}")
        extra_env = {"SPARK_HOME": spark_home}
        worker_name = WorkerName.TASK_EXECUTOR
        worker_id, config_dir, _ = WorkerManager.get_process_dirs(worker_name=worker_name,
                                                                  job_id=task.f_job_id,
                                                                  role=task.f_role,
                                                                  party_id=task.f_party_id,
                                                                  task=task)
        config_path, _ = WorkerManager.get_config(config_dir=config_dir, config=run_parameters)
        # todo: generate main path
        main_path = "/data/projects/fate/python/fate/components/__main__.py"
        cmd = [
            main_path,
            "component",
            "execute",
            "--process-tag",
            task.f_execution_id,
            "--config",
            config_path
        ]
        process_cmd.extend(cmd)
        return WorkerManager.start_task_worker(worker_name=worker_name, task=task,
                                               task_parameters=run_parameters,
                                               extra_env=extra_env, process_cmd=process_cmd, worker_id=worker_id)

    def kill(self, task):
        kill_status_code = process_utils.kill_task_executor_process(task)
        # session stop
        if kill_status_code is KillProcessRetCode.KILLED or task.f_status not in {TaskStatus.WAITING}:
            job_utils.start_session_stop(task)

    def is_alive(self, task):
        return process_utils.check_process(pid=int(task.f_run_pid), task=task)
