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
import subprocess
import sys

import psutil

from fate_arch.common.base_utils import json_dumps, current_timestamp
from fate_arch.common.file_utils import load_json_conf
from fate_flow.utils.log_utils import schedule_logger
from fate_arch.metastore.base_model import auto_date_timestamp_db_field
from fate_flow.db.db_models import DB, Task, WorkerInfo
from fate_flow.db.runtime_config import RuntimeConfig
from fate_flow.entity import ComponentProvider
from fate_flow.entity import RunParameters
from fate_flow.entity.types import WorkerName
from fate_flow.settings import stat_logger
from fate_flow.utils import job_utils, process_utils, base_utils
from fate_flow.utils.log_utils import ready_log, start_log, successful_log, failed_log


class WorkerManager:
    @classmethod
    def start_general_worker(cls, worker_name: WorkerName, job_id="", role="", party_id=0, provider: ComponentProvider = None,
                             initialized_config: dict = None, run_in_subprocess=True, **kwargs):
        if RuntimeConfig.DEBUG:
            run_in_subprocess = True
        participate = locals()
        worker_id, config_dir, log_dir = cls.get_process_dirs(worker_name=worker_name,
                                                              job_id=job_id,
                                                              role=role,
                                                              party_id=party_id)
        if worker_name in [WorkerName.PROVIDER_REGISTRAR, WorkerName.DEPENDENCE_UPLOAD]:
            if not provider:
                raise ValueError("no provider argument")
            config = {
                "provider": provider.to_dict()
            }
            if worker_name == WorkerName.PROVIDER_REGISTRAR:
                from fate_flow.worker.provider_registrar import ProviderRegistrar
                module = ProviderRegistrar
                module_file_path = sys.modules[ProviderRegistrar.__module__].__file__
                specific_cmd = []
            elif worker_name == WorkerName.DEPENDENCE_UPLOAD:
                from fate_flow.worker.dependence_upload import DependenceUpload
                module = DependenceUpload
                module_file_path = sys.modules[DependenceUpload.__module__].__file__
                specific_cmd = [
                    '--dependence_type', kwargs.get("dependence_type")
                ]
            provider_info = provider.to_dict()
        elif worker_name is WorkerName.TASK_INITIALIZER:
            if not initialized_config:
                raise ValueError("no initialized_config argument")
            config = initialized_config
            job_conf = job_utils.save_using_job_conf(job_id=job_id,
                                                     role=role,
                                                     party_id=party_id,
                                                     config_dir=config_dir)

            from fate_flow.worker.task_initializer import TaskInitializer
            module = TaskInitializer
            module_file_path = sys.modules[TaskInitializer.__module__].__file__
            specific_cmd = [
                '--dsl', job_conf["dsl_path"],
                '--runtime_conf', job_conf["runtime_conf_path"],
                '--train_runtime_conf', job_conf["train_runtime_conf_path"],
                '--pipeline_dsl', job_conf["pipeline_dsl_path"],
            ]
            provider_info = initialized_config["provider"]
        else:
            raise Exception(f"not support {worker_name} worker")
        config_path, result_path = cls.get_config(config_dir=config_dir, config=config, log_dir=log_dir)

        process_cmd = [
            sys.executable or "python3",
            module_file_path,
            "--config", config_path,
            '--result', result_path,
            "--log_dir", log_dir,
            "--parent_log_dir", os.path.dirname(log_dir),
            "--worker_id", worker_id,
            "--run_ip", RuntimeConfig.JOB_SERVER_HOST,
            "--job_server", f"{RuntimeConfig.JOB_SERVER_HOST}:{RuntimeConfig.HTTP_PORT}",
        ]

        if job_id:
            process_cmd.extend([
                "--job_id", job_id,
                "--role", role,
                "--party_id", party_id,
            ])

        process_cmd.extend(specific_cmd)
        if run_in_subprocess:
            p = process_utils.run_subprocess(job_id=job_id, config_dir=config_dir, process_cmd=process_cmd,
                                             added_env=cls.get_env(job_id, provider_info), log_dir=log_dir,
                                             cwd_dir=config_dir, process_name=worker_name.value, process_id=worker_id)
            participate["pid"] = p.pid
            if job_id and role and party_id:
                logger = schedule_logger(job_id)
                msg = f"{worker_name} worker {worker_id} subprocess {p.pid}"
            else:
                logger = stat_logger
                msg = f"{worker_name} worker {worker_id} subprocess {p.pid}"
            logger.info(ready_log(msg=msg, role=role, party_id=party_id))

            # asynchronous
            if worker_name in [WorkerName.DEPENDENCE_UPLOAD]:
                if kwargs.get("callback") and kwargs.get("callback_param"):
                    callback_param = {}
                    participate.update(participate.get("kwargs", {}))
                    for k, v in participate.items():
                        if k in kwargs.get("callback_param"):
                            callback_param[k] = v
                    kwargs.get("callback")(**callback_param)
            else:
                try:
                    p.wait(timeout=120)
                    if p.returncode == 0:
                        logger.info(successful_log(msg=msg, role=role, party_id=party_id))
                    else:
                        logger.info(failed_log(msg=msg, role=role, party_id=party_id))
                    if p.returncode == 0:
                        return p.returncode, load_json_conf(result_path)
                    else:
                        std_path = process_utils.get_std_path(log_dir=log_dir, process_name=worker_name.value, process_id=worker_id)
                        raise Exception(f"run error, please check logs: {std_path}, {log_dir}/INFO.log")
                except subprocess.TimeoutExpired as e:
                    err = failed_log(msg=f"{msg} run timeout", role=role, party_id=party_id)
                    logger.exception(err)
                    raise Exception(err)
                finally:
                    try:
                        p.kill()
                        p.poll()
                    except Exception as e:
                        logger.exception(e)
        else:
            kwargs = cls.cmd_to_func_kwargs(process_cmd)
            code, message, result = module().run(**kwargs)
            if code == 0:
                return code, result
            else:
                raise Exception(message)

    @classmethod
    def start_task_worker(cls, worker_name, task: Task, task_parameters: RunParameters = None,
                          executable: list = None, extra_env: dict = None, **kwargs):
        worker_id, config_dir, log_dir = cls.get_process_dirs(worker_name=worker_name,
                                                              job_id=task.f_job_id,
                                                              role=task.f_role,
                                                              party_id=task.f_party_id,
                                                              task=task)

        session_id = job_utils.generate_session_id(task.f_task_id, task.f_task_version, task.f_role, task.f_party_id)
        federation_session_id = job_utils.generate_task_version_id(task.f_task_id, task.f_task_version)

        info_kwargs = {}
        specific_cmd = []
        if worker_name is WorkerName.TASK_EXECUTOR:
            from fate_flow.worker.task_executor import TaskExecutor
            module_file_path = sys.modules[TaskExecutor.__module__].__file__
        else:
            raise Exception(f"not support {worker_name} worker")

        if task_parameters is None:
            task_parameters = RunParameters(**job_utils.get_job_parameters(task.f_job_id, task.f_role, task.f_party_id))

        config = task_parameters.to_dict()
        config["src_user"] = kwargs.get("src_user")
        config_path, result_path = cls.get_config(config_dir=config_dir, config=config, log_dir=log_dir)

        if executable:
            process_cmd = executable
        else:
            process_cmd = [sys.executable or "python3"]

        common_cmd = [
            module_file_path,
            "--job_id", task.f_job_id,
            "--component_name", task.f_component_name,
            "--task_id", task.f_task_id,
            "--task_version", task.f_task_version,
            "--role", task.f_role,
            "--party_id", task.f_party_id,
            "--config", config_path,
            '--result', result_path,
            "--log_dir", log_dir,
            "--parent_log_dir", os.path.dirname(log_dir),
            "--worker_id", worker_id,
            "--run_ip", RuntimeConfig.JOB_SERVER_HOST,
            "--job_server", f"{RuntimeConfig.JOB_SERVER_HOST}:{RuntimeConfig.HTTP_PORT}",
            "--session_id", session_id,
            "--federation_session_id", federation_session_id,
        ]
        process_cmd.extend(common_cmd)
        process_cmd.extend(specific_cmd)
        env = cls.get_env(task.f_job_id, task.f_provider_info)
        if extra_env:
            env.update(extra_env)
        schedule_logger(task.f_job_id).info(
            f"task {task.f_task_id} {task.f_task_version} on {task.f_role} {task.f_party_id} {worker_name} worker subprocess is ready")
        p = process_utils.run_subprocess(job_id=task.f_job_id, config_dir=config_dir, process_cmd=process_cmd,
                                         added_env=env, log_dir=log_dir, cwd_dir=config_dir, process_name=worker_name.value,
                                         process_id=worker_id)
        cls.save_worker_info(task=task, worker_name=worker_name, worker_id=worker_id, run_ip=RuntimeConfig.JOB_SERVER_HOST, run_pid=p.pid, config=config, cmd=process_cmd, **info_kwargs)
        return {"run_pid": p.pid, "worker_id": worker_id, "cmd": process_cmd}

    @classmethod
    def get_process_dirs(cls, worker_name: WorkerName, job_id=None, role=None, party_id=None, task: Task = None):
        worker_id = base_utils.new_unique_id()
        party_id = str(party_id)
        if task:
            config_dir = job_utils.get_job_directory(job_id, role, party_id, task.f_component_name, task.f_task_id,
                                                     str(task.f_task_version), worker_name.value, worker_id)
            log_dir = job_utils.get_job_log_directory(job_id, role, party_id, task.f_component_name)
        elif job_id and role and party_id:
            config_dir = job_utils.get_job_directory(job_id, role, party_id, worker_name.value, worker_id)
            log_dir = job_utils.get_job_log_directory(job_id, role, party_id, worker_name.value, worker_id)
        else:
            config_dir = job_utils.get_general_worker_directory(worker_name.value, worker_id)
            log_dir = job_utils.get_general_worker_log_directory(worker_name.value, worker_id)
        os.makedirs(config_dir, exist_ok=True)
        return worker_id, config_dir, log_dir

    @classmethod
    def get_config(cls, config_dir, config, log_dir):
        config_path = os.path.join(config_dir, "config.json")
        with open(config_path, 'w') as fw:
            fw.write(json_dumps(config))
        result_path = os.path.join(config_dir, "result.json")
        return config_path, result_path

    @classmethod
    def get_env(cls, job_id, provider_info):
        provider = ComponentProvider(**provider_info)
        env = provider.env.copy()
        env["PYTHONPATH"] = os.path.dirname(provider.path)
        if job_id:
            env["FATE_JOB_ID"] = job_id
        return env

    @classmethod
    def cmd_to_func_kwargs(cls, cmd):
        kwargs = {}
        for i in range(2, len(cmd), 2):
            kwargs[cmd[i].lstrip("--")] = cmd[i+1]
        return kwargs

    @classmethod
    @DB.connection_context()
    def save_worker_info(cls, task: Task, worker_name: WorkerName, worker_id, **kwargs):
        worker = WorkerInfo()
        ignore_attr = auto_date_timestamp_db_field()
        for attr, value in task.to_dict().items():
            if hasattr(worker, attr) and attr not in ignore_attr and value is not None:
                setattr(worker, attr, value)
        worker.f_create_time = current_timestamp()
        worker.f_worker_name = worker_name.value
        worker.f_worker_id = worker_id
        for k, v in kwargs.items():
            attr = f"f_{k}"
            if hasattr(worker, attr) and v is not None:
                setattr(worker, attr, v)
        rows = worker.save(force_insert=True)
        if rows != 1:
            raise Exception("save worker info failed")

    @classmethod
    @DB.connection_context()
    def kill_task_all_workers(cls, task: Task):
        schedule_logger(task.f_job_id).info(start_log("kill all workers", task=task))
        workers_info = WorkerInfo.query(task_id=task.f_task_id, task_version=task.f_task_version, role=task.f_role,
                                        party_id=task.f_party_id)
        for worker_info in workers_info:
            schedule_logger(task.f_job_id).info(
                start_log(f"kill {worker_info.f_worker_name}({worker_info.f_run_pid})", task=task))
            try:
                cls.kill_worker(worker_info)
                schedule_logger(task.f_job_id).info(
                    successful_log(f"kill {worker_info.f_worker_name}({worker_info.f_run_pid})", task=task))
            except Exception as e:
                schedule_logger(task.f_job_id).warning(
                    failed_log(f"kill {worker_info.f_worker_name}({worker_info.f_run_pid})", task=task), exc_info=True)
        schedule_logger(task.f_job_id).info(successful_log("kill all workers", task=task))

    @classmethod
    def kill_worker(cls, worker_info: WorkerInfo):
        process_utils.kill_process(pid=worker_info.f_run_pid, expected_cmdline=worker_info.f_cmd)
