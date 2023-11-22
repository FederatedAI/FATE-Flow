
from fate_flow.adapter.bfia.utils.entity.status import JobStatus


from fate_flow.scheduler import SchedulerABC
from fate_flow.utils.log_utils import schedule_logger
from fate_flow.runtime.system_settings import THIRD_PARTY as module_name
from fate_flow.manager.operation.job_saver import JobSaver
from fate_flow.adapter.federated import CommonFederated


class CommonScheduler(SchedulerABC):
    def run_do(self):
        logger = schedule_logger(name="common_scheduler")
        logger.info(f"start schedule {module_name} job")
        jobs = JobSaver.query_job(f_protocol=module_name)
        if jobs:
            for job in jobs:
                if job.f_status not in [JobStatus.FINISHED, JobStatus.REJECTED]:
                    job_id = job.f_job_id
                    resp = CommonFederated.query_job(command_body={"job_id": job_id})
                    status = resp.get("status")
                    if status != job.f_status:
                        JobSaver.update_job({"f_job_id": job_id, "f_status": status})

            schedule_logger().info("schedule ready jobs finished")
