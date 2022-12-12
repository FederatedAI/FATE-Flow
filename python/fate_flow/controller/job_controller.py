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
from arch import current_timestamp
from fate_flow.controller.task_controller import TaskController, TaskParser
from fate_flow.db.db_models import Task
from fate_flow.db.schedule_models import ScheduleTask
from fate_flow.entity.dag_structures import DAGSchema
from fate_flow.entity.run_status import EndStatus, JobStatus, TaskStatus
from fate_flow.entity.task_structures import TaskScheduleSpec, TaskRuntimeInputSpec, RuntimeConfSpec
from fate_flow.entity.types import ReturnCode
from fate_flow.manager.resource_manager import ResourceManager
from fate_flow.operation.job_saver import JobSaver, ScheduleJobSaver
from fate_flow.scheduler.dsl_parser import DagParser
from fate_flow.scheduler.federated_scheduler import FederatedScheduler
from fate_flow.settings import PARTY_ID
from fate_flow.utils import job_utils
from fate_flow.utils.log_utils import schedule_logger


class JobController(object):
    @classmethod
    def request_create_job(cls, dag_schema: dict):
        dag_schema = DAGSchema(**dag_schema)
        dag_schema.dag.conf.initiator_party_id = PARTY_ID
        if not dag_schema.dag.conf.scheduler_party_id:
            dag_schema.dag.conf.scheduler_party_id = PARTY_ID
        response = FederatedScheduler.request_create_job(party_id=dag_schema.dag.conf.scheduler_party_id,
                                                         command_body={
                                                             "dag_schema": dag_schema.dict()
                                                         })
        return response

    @classmethod
    def request_stop_job(cls, job_id, status=None):
        schedule_logger(job_id).info(f"stop job on this party")
        jobs = JobSaver.query_job(job_id=job_id)
        if not jobs:
            return ReturnCode.JOB.NO_FOUND, {}
        kill_status, kill_details = JobController.stop_jobs(job_id=job_id, stop_status=status)
        schedule_logger(job_id).info(f"stop job on this party status {kill_status}")
        schedule_logger(job_id).info(f"request stop job to {status}")
        response = FederatedScheduler.request_stop_job(party_id=jobs[0].f_scheduler_party_id, job_id=job_id, stop_status=status)
        schedule_logger(job_id).info(f"stop job response: {response}")
        return response

    @classmethod
    def create_job(cls, dag_schema: dict, job_id: str, role: str, party_id: str):
        schedule_logger(job_id).info(f"start create job {job_id} {role} {party_id}")
        dag_schema = DAGSchema(**dag_schema)
        job_info = {
            "job_id": job_id,
            "role": role,
            "party_id": party_id,
            "dag": dag_schema.dict(),
            "progress": 0,
            "parties": cls.get_parties_info(dag_schema),
            "initiator_party_id": dag_schema.dag.conf.initiator_party_id,
            "scheduler_party_id": dag_schema.dag.conf.scheduler_party_id,
            "status": JobStatus.READY
        }

        JobSaver.create_job(job_info=job_info)
        cls.create_tasks(job_id, role, party_id, dag_schema)

    @classmethod
    def create_tasks(cls, job_id: str, role: str, party_id: str, dag_schema: DAGSchema, is_scheduler=False):
        schedule_logger(job_id).info(f"start create {'scheduler' if is_scheduler else 'partner'} tasks ...")
        dag_parser = DagParser()
        dag_parser.parse_dag(dag_schema=dag_schema)
        task_list = dag_parser.topological_sort()
        for task_name in task_list:
            cls.create_task(job_id, role, party_id, task_name, dag_schema, dag_parser, is_scheduler)
        schedule_logger(job_id).info("create tasks success")

    @classmethod
    def create_task(cls, job_id, role, party_id, task_name, dag_schema, dag_parser, is_scheduler):

        task_id = job_utils.generate_task_id(job_id=job_id, component_name=task_name)
        task_version = 0
        execution_id = job_utils.generate_session_id(task_id, task_version, role, party_id)
        task_parser = TaskParser(dag_parser=dag_parser, job_id=job_id, task_name=task_name, role=role, party_id=party_id,
                                 task_id=task_id, execution_id=execution_id, task_version=task_version,
                                 parties=dag_schema.dag.parties)
        need_run = task_parser.need_run
        schedule_logger(job_id).info(f"task {task_name} role {role} part id {party_id} need run status {need_run}")
        task_parameters = task_parser.get_task_parameters().dict()
        schedule_logger(job_id).info(f"task {task_name} role {role} part id {party_id} task_parameters"
                                     f" {task_parameters}")
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
                task.f_parties = cls.get_parties_info(dag_schema)
                ScheduleJobSaver.create_task(task.to_human_model_dict())
        else:
            task = Task()
            task.f_job_id = job_id
            task.f_role = role
            task.f_party_id = party_id
            task.f_task_name = task_name
            task.f_component = task_parser.component_ref,
            task.f_task_id = task_id
            task.f_task_version = task_version
            task.f_scheduler_party_id = dag_schema.dag.conf.scheduler_party_id
            task.f_federated_status_collect_type = dag_schema.dag.conf.federated_status_collect_type
            task.f_status = TaskStatus.WAITING if need_run else TaskStatus.PASS
            task.f_party_status = TaskStatus.WAITING
            task.f_component_parameters = task_parameters
            task.f_execution_id = execution_id
            JobSaver.create_task(task.to_human_model_dict())

    @classmethod
    def start_job(cls, job_id, role, party_id, extra_info=None):
        schedule_logger(job_id).info(f"try to start job on {role} {party_id}")
        job_info = {
            "job_id": job_id,
            "role": role,
            "party_id": party_id,
            "status": JobStatus.RUNNING,
            "start_time": current_timestamp()
        }
        if extra_info:
            schedule_logger(job_id).info(f"extra info: {extra_info}")
            job_info.update(extra_info)
        cls.update_job_status(job_info=job_info)
        cls.update_job(job_info=job_info)
        schedule_logger(job_id).info(f"start job on {role} {party_id} successfully")

    @classmethod
    def create_scheduler_tasks_status(cls, job_id, dag_schema):
        schedule_logger(job_id).info("start create schedule task status info")
        dag_parser = DagParser()
        dag_parser.parse_dag(dag_schema=dag_schema)
        task_list = dag_parser.topological_sort()
        for task_name in task_list:
            task_info = {
                "job_id": job_id,
                "task_name": task_name,
                "task_id": job_utils.generate_task_id(job_id=job_id, component_name=task_name),
                "task_version": 0,
                "status": TaskStatus.WAITING
            }
            ScheduleJobSaver.create_task_scheduler_status(task_info)
        schedule_logger(job_id).info("create schedule task status success")

    @classmethod
    def get_parties_info(cls, dag_schema: DAGSchema):
        return [party.dict() for party in dag_schema.dag.parties]

    @classmethod
    def update_job_status(cls, job_info):
        update_status = JobSaver.update_job_status(job_info=job_info)
        if update_status and EndStatus.contains(job_info.get("status")):
            ResourceManager.return_job_resource(
                job_id=job_info["job_id"], role=job_info["role"], party_id=job_info["party_id"])
        return update_status

    @classmethod
    def stop_jobs(cls, job_id, role=None, party_id=None, stop_status=JobStatus.FAILED):
        if not stop_status:
            stop_status = JobStatus.FAILED
        if role and party_id:
            jobs = JobSaver.query_job(
                job_id=job_id, role=role, party_id=party_id)
        else:
            jobs = JobSaver.query_job(job_id=job_id)
        kill_status = True
        kill_details = {}
        for job in jobs:
            kill_job_status, kill_job_details = cls.stop_job(
                job=job, stop_status=stop_status)
            kill_status = kill_status & kill_job_status
            kill_details[job_id] = kill_job_details
        return kill_status, kill_details

    @classmethod
    def stop_job(cls, job, stop_status):
        tasks = JobSaver.query_task(
            job_id=job.f_job_id, role=job.f_role, party_id=job.f_party_id, only_latest=True, reverse=True)
        kill_status = True
        kill_details = {}
        for task in tasks:
            if task.f_status in [TaskStatus.SUCCESS, TaskStatus.WAITING, TaskStatus.PASS]:
                continue
            kill_task_status = TaskController.stop_task(task, stop_status)
            kill_status = kill_status & kill_task_status
            kill_details[task.f_task_id] = 'success' if kill_task_status else 'failed'
        if kill_status:
            job_info = job.to_human_model_dict(only_primary_with=["status"])
            job_info["status"] = stop_status
            JobController.update_job_status(job_info)
        return kill_status, kill_details

    @classmethod
    def update_job(cls, job_info):
        return JobSaver.update_job(job_info=job_info)

    @classmethod
    def query_job(cls, **kwargs):
        query_filters = {}
        for k, v in kwargs.items():
            if v is not None:
                query_filters[k] = v
        return JobSaver.query_job(**query_filters)

    @classmethod
    def query_tasks(cls, **kwargs):
        query_filters = {}
        for k, v in kwargs.items():
            if v is not None:
                query_filters[k] = v
        return JobSaver.query_task(**query_filters)

