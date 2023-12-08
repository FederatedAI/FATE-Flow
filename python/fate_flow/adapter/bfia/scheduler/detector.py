import time

from fate_flow.adapter.bfia.utils.entity.status import TaskStatus
from fate_flow.adapter.bfia.wheels.federated import BfiaFederatedScheduler
from fate_flow.adapter.bfia.wheels.saver import BfiaJobSaver
from fate_flow.engine.devices import build_engine
from fate_flow.utils.cron import Cron
from fate_flow.utils.log_utils import detect_logger


class BfiaDetector(Cron):
    def run_do(self):
        self.logger = detect_logger(log_type="bfia_detector")
        self.detect_running_task()

    def detect_running_task(self):
        self.logger.info('start to detect running task..')
        count = 0
        try:
            running_tasks = BfiaJobSaver.query_task(party_status=TaskStatus.RUNNING)
            self.logger.info(f'running task: {running_tasks}')
            stop_job_ids = set()
            for task in running_tasks:
                try:
                    process_exist = build_engine(task.f_provider_name).is_alive(task)
                    if not process_exist:
                        msg = f"task {task.f_task_id} {task.f_task_version} on {task.f_role} {task.f_party_id}"
                        detect_logger(job_id=task.f_job_id).info(
                            f"{msg} with {task.f_party_status} process {task.f_run_pid} does not exist")
                        time.sleep(3)
                        _tasks = BfiaJobSaver.query_task(task_id=task.f_task_id, task_version=task.f_task_version,
                                                         role=task.f_role, party_id=task.f_party_id)
                        if _tasks:
                            if _tasks[0].f_party_status == TaskStatus.RUNNING:
                                stop_job_ids.add(task.f_job_id)
                                detect_logger(job_id=task.f_job_id).info(
                                    f"{msg} party status has been checked twice, try to stop job")
                            else:
                                detect_logger(job_id=task.f_job_id).info(
                                    f"{msg} party status has changed to {_tasks[0].f_party_status}, may be stopped by task_controller.stop_task, pass stop job again")
                        else:
                            detect_logger(job_id=task.f_job_id).warning(f"{msg} can not found on db")
                except Exception as e:
                    detect_logger(job_id=task.f_job_id).exception(e)
            if stop_job_ids:
                self.logger.info('start to stop jobs: {}'.format(stop_job_ids))
            stop_jobs = set()
            for job_id in stop_job_ids:
                jobs = BfiaJobSaver.query_job(job_id=job_id)
                if jobs:
                    stop_jobs.add(jobs[0])
            self.request_stop_jobs(jobs=stop_jobs, stop_msg="task executor process abort")
        except Exception as e:
            self.logger.exception(e)
        finally:
            self.logger.info(f"finish detect {count} running task")

    def request_stop_jobs(self, jobs, stop_msg):
        if not len(jobs):
            return
        self.logger.info(f"have {len(jobs)} should be stopped, because of {stop_msg}")
        for job in jobs:
            try:
                detect_logger(job_id=job.f_job_id).info(
                    f"detector request start to stop job {job.f_job_id}, because of {stop_msg}")
                status = BfiaFederatedScheduler.request_stop_job(party_id=job.f_scheduler_party_id, job_id=job.f_job_id)
                detect_logger(job_id=job.f_job_id).info(f"detector request stop job {job.f_job_id} {status}")
            except Exception as e:
                detect_logger(job_id=job.f_job_id).exception(e)


