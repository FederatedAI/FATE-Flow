from fate_flow.adapter.bfia.translator.component_spec import BFIAComponentSpec
from fate_flow.adapter.bfia.translator.dsl_translator import Translator
from fate_flow.adapter.bfia.utils.entity.status import StatusSet as BfiaJobStatus
from fate_flow.adapter.bfia.wheels.job import BfiaJobController
from fate_flow.entity.spec.flow import SubmitJobInput, QueryJobInput, QueryJobOutput, StopJobInput, StopJobOutput, \
    QueryTaskOutput, QueryTaskInput, SubmitJobOutput
from fate_flow.entity.types import JobStatus
from fate_flow.manager.service.provider_manager import ProviderManager


class JobController(object):
    @staticmethod
    def create_job(submit_job_input: SubmitJobInput):
        dag_schema = submit_job_input.dag_schema
        components_desc = {}
        for name, desc in ProviderManager.query_component_description(protocol=dag_schema.kind).items():
            components_desc[name] = BFIAComponentSpec.parse_obj(desc)
        bfia_dag = Translator.translate_dag_to_bfia_dag(dag_schema, components_desc)
        job_id = BfiaJobController.request_create_job(
            bfia_dag.dag.dag.dict(exclude_defaults=True),
            bfia_dag.dag.config.dict(exclude_defaults=True),
            bfia_dag.dag.flow_id,
            bfia_dag.dag.old_job_id
        )
        return SubmitJobOutput(job_id=job_id, data=dict(model_id="", model_version=""))

    @classmethod
    def query_job(cls, query_job_input: QueryJobInput):
        jobs = query_job_input.jobs
        for job in jobs:
            job.f_status = cls.update_status(job.f_status)
        return QueryJobOutput(jobs=jobs)

    @classmethod
    def stop_job(cls, stop_job_input: StopJobInput):
        response = BfiaJobController.request_stop_job(stop_job_input.job_id)
        cls.update_response(response)
        return StopJobOutput(**response)

    @classmethod
    def query_task(cls, query_task_input: QueryTaskInput):
        tasks = query_task_input.tasks
        for task in tasks:
            task.f_status = cls.update_status(task.f_status)
            task.f_party_status = cls.update_status(task.f_party_status)
        return QueryTaskOutput(tasks=tasks)

    @staticmethod
    def update_status(status):
        RULES = {
            BfiaJobStatus.PENDING: JobStatus.WAITING,
            BfiaJobStatus.READY: JobStatus.WAITING,
            BfiaJobStatus.RUNNING: JobStatus.RUNNING,
            BfiaJobStatus.FINISHED: JobStatus.SUCCESS,
            BfiaJobStatus.REJECTED: JobStatus.FAILED,
            BfiaJobStatus.SUCCESS: JobStatus.SUCCESS,
            BfiaJobStatus.FAILED: JobStatus.FAILED,

        }
        return RULES[status]

    @staticmethod
    def update_response(response):
        message = response.pop("msg")
        if message:
            response["message"] = message
        return response

