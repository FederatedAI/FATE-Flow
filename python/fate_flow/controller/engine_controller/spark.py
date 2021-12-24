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

from fate_arch.common import EngineType
from fate_flow.controller.engine_controller.engine import EngineABC
from fate_flow.db.db_models import Task
from fate_flow.db.dependence_registry import DependenceRegistry
from fate_flow.entity import ComponentProvider
from fate_flow.entity.run_status import TaskStatus
from fate_flow.entity.types import KillProcessRetCode, WorkerName, FateDependenceName, FateDependenceStorageEngine
from fate_flow.manager.resource_manager import ResourceManager
from fate_flow.manager.worker_manager import WorkerManager
from fate_flow.utils import job_utils, process_utils
from fate_flow.db.service_registry import ServiceRegistry
from fate_flow.settings import DEPENDENT_DISTRIBUTION
from fate_flow.utils.log_utils import schedule_logger


class SparkEngine(EngineABC):
    def run(self, task: Task, run_parameters, run_parameters_path, config_dir, log_dir, cwd_dir, **kwargs):
        spark_home = ServiceRegistry.FATE_ON_SPARK.get("spark", {}).get("home")
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
        spark_submit_config = run_parameters.spark_run

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
        if DEPENDENT_DISTRIBUTION:
            dependence = Dependence()
            dependence.init(provider=ComponentProvider(**task.f_provider_info))
            executor_env_pythonpath, executor_python_env, driver_python_env, archives = dependence.get_task_dependence_info()
            schedule_logger(task.f_job_id).info(f"executor_env_python {executor_python_env}，"
                                                f"driver_env_python {driver_python_env}， archives {archives}")
            executable.append(f'--archives')
            executable.append(archives)
            executable.append(f'--conf')
            executable.append(f'spark.pyspark.python={executor_python_env}')
            executable.append(f'--conf')
            executable.append(f'spark.executorEnv.PYTHONPATH={executor_env_pythonpath}')
            executable.append(f'--conf')
            executable.append(f'spark.pyspark.driver.python={driver_python_env}')
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


class Dependence:
    dependence_config = None

    @classmethod
    def init(cls, provider):
        cls.set_version_dependence(provider)

    @classmethod
    def set_version_dependence(cls, provider, storage_engine=FateDependenceStorageEngine.HDFS.value):
        dependence_config = {}
        for dependence_type in [FateDependenceName.Fate_Source_Code.value, FateDependenceName.Python_Env.value]:
            dependencies_storage_info = DependenceRegistry.get_dependencies_storage_meta(storage_engine=storage_engine,
                                                                                         version=provider.version,
                                                                                         type=dependence_type,
                                                                                         get_or_one=True
                                                                                         )
            dependence_config[dependence_type] = dependencies_storage_info.to_dict()
        cls.dependence_config = dependence_config

    @classmethod
    def get_task_dependence_info(cls):
        return cls.get_executor_env_pythonpath(), cls.get_executor_python_env(), cls.get_driver_python_env(), \
               cls.get_archives()

    @classmethod
    def get_executor_env_pythonpath(cls):
        return cls.dependence_config.get(FateDependenceName.Fate_Source_Code.value).get("f_dependencies_conf").get(
            "executor_env_pythonpath")

    @classmethod
    def get_executor_python_env(cls):
        return cls.dependence_config.get(FateDependenceName.Python_Env.value).get("f_dependencies_conf").get(
            "executor_python")

    @classmethod
    def get_driver_python_env(cls):
        return cls.dependence_config.get(FateDependenceName.Python_Env.value).get("f_dependencies_conf").get(
            "driver_python")

    @classmethod
    def get_archives(cls, storage_engine=FateDependenceStorageEngine.HDFS.value):
        archives = []
        name_node = ResourceManager.get_engine_registration_info(engine_type=EngineType.STORAGE,
                                                                 engine_name=storage_engine
                                                                 ).f_engine_config.get("name_node")
        for dependence_type in [FateDependenceName.Fate_Source_Code.value, FateDependenceName.Python_Env.value]:
            archives.append(
                name_node + cls.dependence_config.get(dependence_type).get("f_dependencies_conf").get("archives")
            )
        return ','.join(archives)
