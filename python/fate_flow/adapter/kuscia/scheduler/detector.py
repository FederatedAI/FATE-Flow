
from fate_flow.adapter.bfia.utils.entity.status import JobStatus
from fate_flow.utils.log_utils import schedule_logger
from fate_flow.manager.operation.job_saver import JobSaver
from fate_flow.adapter.kuscia.federated import Federated
from fate_flow.utils.cron import Cron
from fate_flow.utils.log_utils import detect_logger


class CommonScheduler(Cron):
    def run_do(self):
        self.logger = detect_logger(log_type="kuscia_detector")
        self.detect_query_job()

    def detect_query_job(self):
        self.logger.info(f'start to detect kuscia query job...')
        jobs = JobSaver.query_job(f_protocol="kuscia")
        if jobs:
            for job in jobs:
                if job.f_status not in [JobStatus.FINISHED, JobStatus.REJECTED]:
                    job_id = job.f_job_id
                    resp = Federated.query_job(command_body={"job_id": job_id})
                    status = resp.get("status")
                    if status != job.f_status:
                        JobSaver.update_job({"f_job_id": job_id, "f_status": status})

            schedule_logger().info("schedule ready jobs finished")
