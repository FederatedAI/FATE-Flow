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
from fate_flow.controller.task_controller import TaskController
from fate_flow.entity.spec import DAGSchema, JobConfSpec
from fate_flow.entity.types import EndStatus, JobStatus, TaskStatus
from fate_flow.entity.code import ReturnCode
from fate_flow.manager.resource_manager import ResourceManager
from fate_flow.operation.job_saver import JobSaver
from fate_flow.scheduler.federated_scheduler import FederatedScheduler
from fate_flow.settings import PARTY_ID
from fate_flow.utils.base_utils import current_timestamp
from fate_flow.utils.log_utils import schedule_logger


class JobController(object):
    @classmethod
    def request_create_job(cls, dag_schema: dict):
        dag_schema = DAGSchema(**dag_schema)
        if not dag_schema.dag.conf:
            dag_schema.dag.conf = JobConfSpec()
        dag_schema.dag.conf.initiator_party_id = PARTY_ID
        if not dag_schema.dag.conf.scheduler_party_id:
            dag_schema.dag.conf.scheduler_party_id = PARTY_ID
        response = FederatedScheduler.request_create_job(
            party_id=dag_schema.dag.conf.scheduler_party_id,
            command_body={
                "dag_schema": dag_schema.dict()
            })
        return response

    @classmethod
    def request_stop_job(cls, job_id):
        schedule_logger(job_id).info(f"stop job on this party")
        jobs = JobSaver.query_job(job_id=job_id)
        if not jobs:
            return {"code": ReturnCode.Job.NOT_FOUND, "message": "job not found"}
        status = JobStatus.CANCELED
        kill_status, kill_details = JobController.stop_jobs(job_id=job_id, stop_status=status)
        schedule_logger(job_id).info(f"stop job on this party status {kill_status}")
        schedule_logger(job_id).info(f"request stop job to {status}")
        response = FederatedScheduler.request_stop_job(
            party_id=jobs[0].f_scheduler_party_id,
            job_id=job_id, stop_status=status
        )
        schedule_logger(job_id).info(f"stop job response: {response}")
        return response

    @classmethod
    def request_rerun_job(cls, job):
        schedule_logger(job.f_job_id).info(f"request rerun job {job.f_job_id}")
        response = FederatedScheduler.request_rerun_job(party_id=job.f_scheduler_party_id, job_id=job.f_job_id)
        schedule_logger(job.f_job_id).info(f"rerun job response: {response}")
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
            "parties": [party.dict() for party in dag_schema.dag.parties],
            "initiator_party_id": dag_schema.dag.conf.initiator_party_id,
            "scheduler_party_id": dag_schema.dag.conf.scheduler_party_id,
            "status": JobStatus.READY,
            "model_id": dag_schema.dag.conf.model_id,
            "model_version": dag_schema.dag.conf.model_version
        }
        JobSaver.create_job(job_info=job_info)
        TaskController.create_tasks(job_id, role, party_id, dag_schema)

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
