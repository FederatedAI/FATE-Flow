
from fate_flow.adapter.bfia.utils.entity.code import ReturnCode
from fate_flow.entity.types import JobStatus
from fate_flow.adapter.kuscia.federated import Federated
from fate_flow.db import Job, Task
from fate_flow.manager.operation.job_saver import JobSaver
from fate_flow.utils.job_utils import generate_job_id
from fate_flow.utils.log_utils import schedule_logger

from fate_flow.adapter.kuscia.spec.job import DagSchemaSpec


class JobController(object):

    @classmethod
    def request_create_job(cls, dag_schema):
        job_id = generate_job_id()
        dag_schema = DagSchemaSpec(**dag_schema)
        schedule_logger(job_id).info(f"create job {job_id}")
        job = Job()
        job.f_job_id = job_id
        job.f_role = ""
        job.f_party_id = ""
        job.f_dag = dag_schema.dict()
        job.f_progress = 0
        job.f_parties = cls.get_job_parties(dag_schema)
        job.f_initiator_party_id = ""
        job.f_scheduler_party_id = ""
        job.f_status = JobStatus.WAITING
        job.f_model_id = job_id
        job.f_model_version = "0"
        job.f_module_name = dag_schema.kind
        JobSaver.create_job(job_info=job.to_human_model_dict())

        schedule_logger(job_id).info("start request create job")
        tasks = cls.get_job_tasks(dag_schema.spec.tasks)
        job_info = {
            "job_id": job_id,
            "initiator": dag_schema.spec.initiator,
            "max_parallelism": dag_schema.spec.maxParallelism,
            "tasks": tasks
        }
        resp = Federated.create_job(command_body=job_info)
        schedule_logger(job_id).info(f"response: {resp}")
        if resp and isinstance(resp, dict) and resp.get("code") == ReturnCode.SUCCESS:
            job.f_status = JobStatus.SUCCESS
            JobSaver.create_job(job_info=job.to_human_model_dict())
            return job_id
        else:
            raise RuntimeError(resp)

    @classmethod
    def query_job_status(cls, job_id):

        jobs = JobSaver.query_job(job_id=job_id)
        if jobs[0].f_status != JobStatus.SUCCESS:
            resp = Federated.query_job(command_body={"job_id": job_id})

        return {"status": jobs[0].f_status}

    @classmethod
    def query_job_batch(cls, job_ids: list):
        resp = Federated.query_job_batch(command_body={"job_ids": job_ids})
        return resp

    @classmethod
    def request_stop_job(cls, job_id):
        jobs = JobSaver.query_job(job_id=job_id)
        if not jobs:
            raise RuntimeError("No found jobs")

        schedule_logger(job_id).info(f"request stop job")
        response = Federated.stop_job(command_body={"job_id": job_id})
        schedule_logger(job_id).info(f"stop job response: {response}")
        return response

    @staticmethod
    def get_job_parties(dag_schema: DagSchemaSpec):
        task = dag_schema.spec.tasks[0]
        parties_list = task.parties
        return set(
            parties.domainID for parties in parties_list
        )

    @staticmethod
    def get_job_tasks(tasks):
        task_list = []
        for task in tasks:
            dct = {
                "app_image": task.appImage,
                "parties": task.parties,
                "alias": task.alias,
                "task_id": task.taskID,
                "task_input_config": task.taskInputConfig,
                "priority": task.priority,
            }
            if task.dependencies:
                dct["dependencies"] = task.dependencies
            task_list.append(dct)
        return task_list

    # @classmethod
    # def update_job(cls, job_info):
    #     return JobSaver.update_job(job_info=job_info)
