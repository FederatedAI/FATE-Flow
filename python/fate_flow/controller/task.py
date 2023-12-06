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
import copy
import os

import yaml

from fate_flow.controller.parser import JobParser
from fate_flow.db.db_models import Task
from fate_flow.db.schedule_models import ScheduleTask, ScheduleJob, ScheduleTaskStatus
from fate_flow.engine.devices import build_engine, EngineABC
from fate_flow.entity.spec.dag import DAGSchema, LauncherSpec
from fate_flow.manager.service.resource_manager import ResourceManager
from fate_flow.manager.service.worker_manager import WorkerManager
from fate_flow.runtime.job_default_config import JobDefaultConfig
from fate_flow.runtime.runtime_config import RuntimeConfig
from fate_flow.controller.federated import FederatedScheduler
from fate_flow.entity.types import EndStatus, TaskStatus, FederatedCommunicationType, LauncherType
from fate_flow.entity.code import FederatedSchedulingStatusCode
from fate_flow.manager.operation.job_saver import JobSaver, ScheduleJobSaver
from fate_flow.utils import job_utils
from fate_flow.utils.base_utils import current_timestamp
from fate_flow.utils.log_utils import schedule_logger


class TaskController(object):
    INITIATOR_COLLECT_FIELDS = ["status", "party_status", "start_time", "update_time", "end_time", "elapsed"]

    @classmethod
    def create_tasks(cls, job_id: str, role: str, party_id: str, dag_schema: DAGSchema, task_run=None, task_cores=None,
                     is_scheduler=False):
        schedule_logger(job_id).info(f"start create {'scheduler' if is_scheduler else 'partner'} tasks ...")
        job_parser = JobParser(dag_schema)
        task_list = job_parser.topological_sort()
        for task_name in task_list:
            cls.create_task(job_id, role, party_id, task_name, dag_schema, job_parser, task_run=task_run,
                            is_scheduler=is_scheduler, task_cores=task_cores)
        schedule_logger(job_id).info("create tasks success")

    @classmethod
    def create_task(cls, job_id, role, party_id, task_name, dag_schema, job_parser, is_scheduler, task_run=None,
                    task_cores=None, task_version=0):
        task_id = job_utils.generate_task_id(job_id=job_id, component_name=task_name)
        execution_id = job_utils.generate_session_id(task_id, task_version, role, party_id)
        task_node = job_parser.get_task_node(task_name=task_name)
        task_parser = job_parser.task_parser(
            task_node=task_node, job_id=job_id, task_name=task_name, role=role, party_id=party_id,
            task_id=task_id, execution_id=execution_id, task_version=task_version, parties=dag_schema.dag.parties,
            model_id=dag_schema.dag.conf.model_id, model_version=dag_schema.dag.conf.model_version
        )
        need_run = task_parser.need_run
        schedule_logger(job_id).info(f"task {task_name} role {role} part id {party_id} need run status {need_run}")
        if is_scheduler:
            if need_run:
                task = ScheduleTask()
                task.f_job_id = job_id
                task.f_role = role
                task.f_party_id = party_id
                task.f_task_name = task_name
                task.f_component = task_parser.component_ref
                task.f_task_id = task_id
                task.f_task_version = task_version
                task.f_status = TaskStatus.WAITING
                task.f_parties = [party.dict() for party in dag_schema.dag.parties]
                ScheduleJobSaver.create_task(task.to_human_model_dict())
        else:
            task_parameters = task_parser.task_parameters
            task_parameters.engine_run = task_run
            task_parameters.computing_partitions = dag_schema.dag.conf.computing_partitions
            schedule_logger(job_id).info(f"task {task_name} role {role} part id {party_id} task_parameters"
                                         f" {task_parameters.dict()}, provider: {task_parser.provider}")
            task = Task()
            task.f_job_id = job_id
            task.f_role = role
            task.f_party_id = party_id
            task.f_task_name = task_name
            task.f_component = task_parser.component_ref
            task.f_task_id = task_id
            task.f_task_version = task_version
            task.f_scheduler_party_id = dag_schema.dag.conf.scheduler_party_id
            task.f_status = TaskStatus.WAITING if need_run else TaskStatus.PASS
            task.f_party_status = TaskStatus.WAITING
            task.f_execution_id = execution_id
            task.f_provider_name = task_parser.provider
            task.f_timeout = task_parser.timeout
            task.f_sync_type = dag_schema.dag.conf.sync_type
            task.f_task_run = task_run
            task.f_task_cores = task_cores
            cls.update_local(task)
            cls.update_launcher_config(task, task_parser.task_runtime_launcher, task_parameters)
            task.f_component_parameters = task_parameters.dict()
            status = JobSaver.create_task(task.to_human_model_dict())
            schedule_logger(job_id).info(task.to_human_model_dict())
            schedule_logger(job_id).info(status)

    @staticmethod
    def update_local(task):
        # HA need route to local
        if task.f_role == "local":
            task.f_run_ip = RuntimeConfig.JOB_SERVER_HOST
            task.f_run_port = RuntimeConfig.HTTP_PORT

    @staticmethod
    def update_launcher_config(task, task_runtime_launcher, task_parameters):
        # support deepspeed and other launcher
        if task.f_role == "arbiter":
            return
        schedule_logger(task.f_job_id).info(f"task runtime launcher: {task_runtime_launcher}")
        launcher = LauncherSpec.parse_obj(task_runtime_launcher)
        if launcher.name and launcher.name != LauncherType.DEFAULT:
            task_parameters.launcher_name = task.f_launcher_name = launcher.name
            launcher_conf = copy.deepcopy(JobDefaultConfig.launcher.get(task_parameters.launcher_name))
            if launcher.conf:
                launcher_conf.update(launcher.conf)
            task_parameters.launcher_conf = task.f_launcher_conf = launcher_conf

    @staticmethod
    def create_schedule_tasks(job: ScheduleJob, dag_schema):
        for party in job.f_parties:
            role = party.get("role")
            party_ids = party.get("party_id")
            for party_id in party_ids:
                TaskController.create_tasks(job.f_job_id, role, party_id, dag_schema, is_scheduler=True)
        TaskController.create_scheduler_tasks_status(job.f_job_id, dag_schema)

    @classmethod
    def create_scheduler_tasks_status(cls, job_id, dag_schema, task_version=0, auto_retries=None, task_name=None):
        schedule_logger(job_id).info("start create schedule task status info")
        job_parser = JobParser(dag_schema)
        if task_name:
            task_list = [task_name]
        else:
            task_list = job_parser.topological_sort()
        for _task_name in task_list:
            task_info = {
                "job_id": job_id,
                "task_name": _task_name,
                "task_id": job_utils.generate_task_id(job_id=job_id, component_name=_task_name),
                "task_version": task_version,
                "status": TaskStatus.WAITING,
                "auto_retries": dag_schema.dag.conf.auto_retries if auto_retries is None else auto_retries,
                "sync_type": dag_schema.dag.conf.sync_type
            }
            ScheduleJobSaver.create_task_scheduler_status(task_info)
        schedule_logger(job_id).info("create schedule task status success")

    @classmethod
    def start_task(cls, task: Task):
        job_id = task.f_job_id
        role = task.f_role
        party_id = task.f_party_id
        task_id = task.f_task_id
        task_version = task.f_task_version
        schedule_logger(job_id).info(
            f"try to start task {task_id} {task_version} on {role} {party_id} executor subprocess")
        task_executor_process_start_status = False
        task_info = {
            "job_id": job_id,
            "task_id": task_id,
            "task_version": task_version,
            "role": role,
            "party_id": party_id,
        }
        is_failed = False
        try:
            run_parameters = task.f_component_parameters
            schedule_logger(job_id).info(f"task run parameters: {run_parameters}")
            task_executor_process_start_status = False

            config_dir = job_utils.get_task_directory(
                job_id, role, party_id, task.f_task_name, task.f_task_version, input=True
            )
            os.makedirs(config_dir, exist_ok=True)
            run_parameters_path = os.path.join(config_dir, 'preprocess_parameters.yaml')
            with open(run_parameters_path, 'w') as fw:
                yaml.dump(run_parameters, fw)
            backend_engine = cls.build_task_engine(task.f_provider_name, task.f_launcher_name)
            run_info = backend_engine.run(
                task=task,
                run_parameters=run_parameters,
                run_parameters_path=run_parameters_path,
                config_dir=config_dir,
                log_dir=job_utils.get_job_log_directory(job_id, role, party_id, task.f_task_name),
                cwd_dir=job_utils.get_job_directory(job_id, role, party_id, task.f_task_name)
            )
            task_info.update(run_info)
            task_info["start_time"] = current_timestamp()
            task_executor_process_start_status = True
        except Exception as e:
            schedule_logger(job_id).exception(e)
            is_failed = True
        finally:
            try:
                cls.update_task(task_info=task_info)
                task_info["party_status"] = TaskStatus.RUNNING
                cls.update_task_status(task_info=task_info)
                if is_failed:
                    task_info["party_status"] = TaskStatus.FAILED
                    cls.update_task_status(task_info=task_info)
            except Exception as e:
                schedule_logger(job_id).exception(e)
            schedule_logger(job_id).info(
                "task {} {} on {} {} executor subprocess start {}".format(
                    task_id, task_version, role, party_id, "success" if task_executor_process_start_status else "failed"
                ))
        return not is_failed

    @classmethod
    def create_new_version_task(cls, task: Task, new_version):
        jobs = JobSaver.query_job(job_id=task.f_job_id, role=task.f_role, party_id=task.f_party_id)
        if not jobs:
            return False
        dag_schema = DAGSchema(**jobs[0].f_dag)
        job_parser = JobParser(dag_schema)
        cls.create_task(
            task.f_job_id, task.f_role, task.f_party_id, task.f_task_name, dag_schema, job_parser,
            task_run=task.f_task_run, task_cores=task.f_task_cores, is_scheduler=False, task_version=new_version
        )

    @classmethod
    def create_new_version_schedule_task(cls, job, task, auto):
        # stop old version task
        FederatedScheduler.stop_task(task_id=task.f_task_id, command_body={"status": task.f_status})
        # create new version task
        task.f_task_version = task.f_task_version + 1
        if auto:
            task.f_auto_retries = task.f_auto_retries - 1
        status_code, response = FederatedScheduler.rerun_task(task_id=task.f_task_id, task_version=task.f_task_version)
        dag_schema = DAGSchema(**job.f_dag)
        if status_code != FederatedSchedulingStatusCode.SUCCESS:
            raise Exception(f"create {task.f_task_id} new version failed")
        job_parser = JobParser(dag_schema)
        for party in job.f_parties:
            _role = party.get("role")
            for _party_id in party.get("party_id"):
                cls.create_task(
                    job.f_job_id, _role, _party_id, task.f_task_name, dag_schema, job_parser,
                    is_scheduler=True, task_version=task.f_task_version
                )
        TaskController.create_scheduler_tasks_status(
            job.f_job_id,
            dag_schema,
            task_version=task.f_task_version,
            auto_retries=task.f_auto_retries,
            task_name=task.f_task_name
        )
        schedule_logger(job.f_job_id).info(f"create task {task.f_task_id} new version {task.f_task_version} successfully")

    @classmethod
    def prepare_rerun_task(cls, job: ScheduleJob, task: ScheduleTaskStatus, auto=False, force=False):
        job_id = job.f_job_id
        can_rerun = False
        if force:
            can_rerun = True
            auto = False
            schedule_logger(job_id).info(
                f"task {task.f_task_id} {task.f_task_version} with {task.f_status} was forced to rerun")
        elif task.f_status in {TaskStatus.SUCCESS}:
            schedule_logger(job_id).info(
                f"task {task.f_task_id} {task.f_task_version} is {task.f_status} and not force reruen, pass rerun")
        elif auto and task.f_auto_retries < 1:
            schedule_logger(job_id).info(f"task {task.f_task_id} has no retry count, pass rerun")
        else:
            can_rerun = True
        if can_rerun:
            if task.f_status != TaskStatus.WAITING:
                cls.create_new_version_schedule_task(job=job, task=task, auto=auto)
        return can_rerun

    @classmethod
    def update_task(cls, task_info):
        update_status = False
        try:
            update_status = JobSaver.update_task(task_info=task_info)
        except Exception as e:
            schedule_logger(task_info["job_id"]).exception(e)
        finally:
            return update_status

    @classmethod
    def update_task_status(cls, task_info, scheduler_party_id=None, sync_type=None):
        task = JobSaver.query_task(
            task_id=task_info.get("task_id"),
            task_version=task_info.get("task_version")
        )[0]
        scheduler_party_id, sync_type = task.f_scheduler_party_id, task.f_sync_type
        update_status = JobSaver.update_task_status(task_info=task_info)
        if update_status and EndStatus.contains(task_info.get("party_status")):
            ResourceManager.return_task_resource(**task_info)
        if "party_status" in task_info:
            report_task_info = {
                "job_id": task_info.get("job_id"),
                "role": task_info.get("role"),
                "party_id": task_info.get("party_id"),
                "task_id": task_info.get("task_id"),
                "task_version": task_info.get("task_version"),
                "status": task_info.get("party_status")
            }
            if sync_type == FederatedCommunicationType.CALLBACK:
                cls.report_task_to_scheduler(task_info=report_task_info, scheduler_party_id=scheduler_party_id)
        if update_status and EndStatus.contains(task_info.get("party_status")):
            cls.callback_task_output(task)
        return update_status

    @classmethod
    def report_task_to_scheduler(cls, task_info, scheduler_party_id):
        FederatedScheduler.report_task_to_scheduler(party_id=scheduler_party_id, command_body=task_info)

    @classmethod
    def collect_task(cls, job_id, task_id, task_version, role, party_id):
        tasks = JobSaver.query_task(job_id=job_id, task_id=task_id,  task_version=task_version, role=role,
                                    party_id=party_id)
        if tasks:
            return tasks[0].to_human_model_dict(only_primary_with=cls.INITIATOR_COLLECT_FIELDS)
        else:
            return None

    @classmethod
    def stop_task(cls, task: Task, stop_status):
        kill_status = cls.kill_task(task=task)
        task_info = {
            "job_id": task.f_job_id,
            "task_id": task.f_task_id,
            "task_version": task.f_task_version,
            "role": task.f_role,
            "party_id": task.f_party_id,
            "party_status": stop_status,
            "kill_status": True
        }
        cls.update_task_status(task_info=task_info, scheduler_party_id=task.f_scheduler_party_id, sync_type=task.f_sync_type)
        cls.update_task(task_info=task_info)
        return kill_status

    @classmethod
    def kill_task(cls, task: Task):
        kill_status = False
        try:
            backend_engine = cls.build_task_engine(task.f_provider_name, task.f_launcher_name)
            if backend_engine:
                backend_engine.kill(task)
                backend_engine.cleanup(task)
            WorkerManager.kill_task_all_workers(task)
        except Exception as e:
            schedule_logger(task.f_job_id).exception(e)
        else:
            kill_status = True
        finally:
            schedule_logger(task.f_job_id).info(
                'task {} {} on {} {} process {} kill {}'.format(
                    task.f_task_id,
                    task.f_task_version,
                    task.f_role,
                    task.f_party_id,
                    task.f_run_pid,
                    'success' if kill_status else 'failed'
                ))
            return kill_status

    @classmethod
    def clean_task(cls, task):
        try:
            backend_engine = cls.build_task_engine(task.f_provider_name, task.f_launcher_name)
            if backend_engine:
                schedule_logger(task.f_job_id).info(f"start clean task:[{task.f_task_id} {task.f_task_version}]")
                backend_engine.cleanup(task)
            WorkerManager.kill_task_all_workers(task)
        except Exception as e:
            schedule_logger(task.f_job_id).exception(e)

    @classmethod
    def build_task_engine(cls, provider_name, launcher_name=LauncherType.DEFAULT) -> EngineABC:
        return build_engine(provider_name, launcher_name)

    @classmethod
    def callback_task_output(cls, task: Task):
        if task.f_launcher_name == LauncherType.DEEPSPEED:
            engine = cls.build_task_engine(provider_name=task.f_provider_name, launcher_name=task.f_launcher_name)
            engine.download_output(task)
