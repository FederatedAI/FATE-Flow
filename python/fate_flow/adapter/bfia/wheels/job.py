from copy import deepcopy

from fate_flow.adapter.bfia.wheels.parser import get_dag_parser

from fate_flow.adapter.bfia.settings import LOCAL_SITE_ID as PARTY_ID
from fate_flow.adapter.bfia.utils.entity.code import ReturnCode
from fate_flow.adapter.bfia.utils.entity.status import TaskStatus, JobStatus, EndStatus
from fate_flow.adapter.bfia.utils.spec.job import DagSchemaSpec
from fate_flow.adapter.bfia.wheels.federated import BfiaFederatedScheduler
from fate_flow.adapter.bfia.wheels.task import BfiaTaskController
from fate_flow.db import Job
from fate_flow.adapter.bfia.wheels.saver import BfiaJobSaver as JobSaver
from fate_flow.utils.base_utils import current_timestamp
from fate_flow.utils.job_utils import save_job_dag, generate_job_id
from fate_flow.utils.log_utils import schedule_logger


class BfiaJobController(object):
    @classmethod
    def request_create_job(cls, dag, config, flow_id, old_job_id):
        job_id = generate_job_id()
        job_info = {
            "dag": dag,
            "config": config,
            "flow_id": flow_id,
            "old_job_id": old_job_id,
            "job_id": job_id
        }
        schedule_logger(job_id).info("start request create job")
        resp = BfiaFederatedScheduler.request_create_job(
            party_id=PARTY_ID,
            command_body=job_info
        )
        schedule_logger(job_id).info(f"response: {resp}")
        if resp and isinstance(resp, dict) and resp.get("code") == ReturnCode.SUCCESS:
            save_job_dag(job_id=job_id, dag=job_info)
            return job_id
        else:
            raise RuntimeError(resp)

    @classmethod
    def query_job_status(cls, **kwargs):
        all_status = {}
        status = {}
        jobs = JobSaver.query_job(**kwargs)
        for job in jobs:
            if job.f_job_id not in all_status:
                all_status[job.f_job_id] = [job.f_status]

        for job_id, status_list in all_status.items():
            status[job_id] = cls.calculate_multi_party_job_status(status_list)

        return status

    @classmethod
    def request_stop_job(cls, job_id):
        jobs = JobSaver.query_job(
            job_id=job_id
        )
        if not jobs:
            raise RuntimeError("No found jobs")

        schedule_logger(job_id).info(f"stop job on this party")
        cls.stop_local_jobs(job_id=job_id)

        schedule_logger(job_id).info(f"request stop job")
        response = BfiaFederatedScheduler.request_stop_job(
            party_id=jobs[0].f_scheduler_party_id,
            job_id=job_id
        )
        schedule_logger(job_id).info(f"stop job response: {response}")
        return response

    @classmethod
    def create_local_jobs(cls, job_id, dag):
        schedule_logger(job_id).info(f"start create job {job_id}")
        schedule_logger(job_id).info(f"job dag schema: {dag}")
        dag_schema = DagSchemaSpec(**dag)
        for role, node_id_list in dag_schema.dag.config.role.dict().items():
            if node_id_list and PARTY_ID in node_id_list:
                cls.create_local_job(job_id, role, PARTY_ID, dag_schema)
        schedule_logger(job_id).info(f"create job {job_id} success")

    @classmethod
    def create_local_job(cls, job_id, role, node_id, dag_schema: DagSchemaSpec):
        schedule_logger(job_id).info(f"create job {job_id} role {role}")
        job = Job()
        job.f_flow_id = dag_schema.dag.flow_id
        job.f_protocol = dag_schema.kind
        job.f_job_id = job_id
        job.f_role = role
        job.f_party_id = node_id
        job.f_dag = dag_schema.dict()
        job.f_progress = 0
        job.f_parties = cls.get_job_parties(dag_schema)
        job.f_initiator_party_id = dag_schema.dag.config.initiator.node_id
        job.f_scheduler_party_id = dag_schema.dag.config.initiator.node_id
        job.f_status = JobStatus.READY
        job.f_model_id = job_id
        job.f_model_version = "0"
        JobSaver.create_job(job_info=job.to_human_model_dict())

    @classmethod
    def start_job(cls, job_id):
        schedule_logger(job_id).info(f"try to start job")
        job_info = {
            "job_id": job_id,
            "start_time": current_timestamp()
        }
        cls.update_job_info(job_info=job_info, callback=cls.update_job)
        job_info["status"] = JobStatus.RUNNING
        cls.update_job_info(job_info=job_info, callback=cls.update_job_status)
        schedule_logger(job_id).info(f"start job on status {job_info.get('status')}")

    @classmethod
    def update_job_info(cls, job_info, callback):
        info = deepcopy(job_info)
        if "role" not in job_info or "party_id" not in job_info:
            job_list = JobSaver.query_job(job_id=job_info.get("job_id"))
            for job in job_list:
                info["role"] = job.f_role
                info["party_id"] = job.f_party_id
                callback(info)
        else:
            callback(info)

    @classmethod
    def update_job_status(cls, job_info):
        update_status = JobSaver.update_job_status(job_info=job_info)
        if update_status and EndStatus.contains(job_info.get("status")):
            pass

    @classmethod
    def update_job(cls, job_info):
        return JobSaver.update_job(job_info=job_info)

    @staticmethod
    def get_job_parties(dag_schema: DagSchemaSpec):
        return set(
            value for values_list in dag_schema.dag.config.role.dict().values() if values_list for value in values_list
        )

    @classmethod
    def stop_local_jobs(cls, job_id, task_name=None):
        jobs = JobSaver.query_job(
            job_id=job_id
        )

        for job in jobs:
            cls.stop_job(job=job, task_name=task_name)

    @classmethod
    def stop_job(cls, job, task_name):
        stop_status = TaskStatus.FAILED
        schedule_logger(job_id=job.f_job_id).info("start stop job on local")
        # get tasks
        if task_name:
            tasks = JobSaver.query_task(
                job_id=job.f_job_id, role=job.f_role, party_id=job.f_party_id,
                only_latest=True, reverse=True, task_name=task_name
            )
        else:
            tasks = JobSaver.query_task(
                job_id=job.f_job_id, role=job.f_role, party_id=job.f_party_id,
                only_latest=True, reverse=True
            )
        update_job = False
        # stop tasks
        for task in tasks:
            if task.f_party_status == TaskStatus.FAILED:
                update_job = True
            # if task.f_status in [TaskStatus.SUCCESS, TaskStatus.PENDING, TaskStatus.READY]:
            #     continue
            schedule_logger(job_id=job.f_job_id).info(f"[stop]start to kill task {task.f_task_name} "
                                                      f"status {task.f_party_status}")
            status = BfiaTaskController.stop_task(task, stop_status=stop_status)
            schedule_logger(job_id=job.f_job_id).info(f"[stop]Kill {task.f_task_name} task completed: {status}")

        # update job status
        if update_job or cls.calculate_job_is_finished(job):
            BfiaJobController.update_job_status({
                "job_id": job.f_job_id,
                "role": job.f_role,
                "party_id": job.f_party_id,
                "status": JobStatus.FINISHED
            })

    @classmethod
    def calculate_job_is_finished(cls, job):
        schedule_logger(job.f_job_id).info("start to calculate job status")
        dag_schema = DagSchemaSpec.parse_obj(job.f_dag)
        job_parser = get_dag_parser(dag_schema)
        task_list = job_parser.party_topological_sort(role=job.f_role, party_id=job.f_party_id)
        waiting_list = []
        for name in task_list:
            tasks = JobSaver.query_task(
                job_id=job.f_job_id, role=job.f_role, party_id=job.f_party_id,
                only_latest=True, reverse=True, task_name=name
            )
            if not tasks:
                waiting_list.append(name)
        if waiting_list:
            schedule_logger(job.f_job_id).info(f"task {waiting_list} is waiting to run")
            return False
        return True

    @classmethod
    def calculate_multi_party_job_status(cls, party_status):
        tmp_status_set = set(party_status)
        if len(tmp_status_set) == 1:
            return tmp_status_set.pop()
        else:
            if JobStatus.REJECTED in tmp_status_set:
                return JobStatus.REJECTED
            if JobStatus.FINISHED in tmp_status_set:
                return JobStatus.FINISHED
            if JobStatus.RUNNING in tmp_status_set:
                return JobStatus.RUNNING
            if JobStatus.READY in tmp_status_set:
                return JobStatus.READY
            if JobStatus.PENDING in tmp_status_set:
                return JobStatus.PENDING
