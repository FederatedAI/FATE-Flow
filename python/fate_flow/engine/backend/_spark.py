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

from fate_flow.engine.backend._base import LocalEngine
from fate_flow.entity.types import WorkerName
from fate_flow.manager.service.worker_manager import WorkerManager


class SparkEngine(LocalEngine):
    def run(self, task_info, run_parameters, conf_path, output_path, engine_run, provider_name, **kwargs):
        spark_home = os.environ.get("SPARK_HOME", None)
        if not spark_home:
            try:
                import pyspark
                spark_home = pyspark.__path__[0]
            except ImportError as e:
                raise RuntimeError("can not import pyspark")
            except Exception as e:
                raise RuntimeError("can not import pyspark")

        deploy_mode = engine_run.get("deploy-mode", "client")
        if deploy_mode not in ["client"]:
            raise ValueError(f"deploy mode {deploy_mode} not supported")

        spark_submit_cmd = os.path.join(spark_home, "bin/spark-submit")
        process_cmd = [spark_submit_cmd, f"--name={task_info.get('task_id')}#{task_info.get('role')}"]
        for k, v in engine_run.items():
            if k != "conf":
                process_cmd.append(f"--{k}={v}")
        if "conf" in engine_run:
            for ck, cv in engine_run["conf"].items():
                process_cmd.append(f"--conf")
                process_cmd.append(f"{ck}={cv}")
        extra_env = {"SPARK_HOME": spark_home}
        return WorkerManager.start_task_worker(
            worker_name=WorkerName.TASK_EXECUTE,
            task_info=task_info,
            common_cmd=self.generate_component_run_cmd(provider_name, conf_path, output_path),
            extra_env=extra_env,
            executable=process_cmd,
            sync=True
        ).returncode
