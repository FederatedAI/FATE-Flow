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
import time

from fate_flow.engine.devices import build_engine
from fate_flow.entity.types import TaskStatus, JobStatus
from fate_flow.operation.job_saver import JobSaver
from fate_flow.runtime.runtime_config import RuntimeConfig
from fate_flow.scheduler.federated_scheduler import FederatedScheduler
from fate_flow.utils.cron import Cron
from fate_flow.utils.log_utils import detect_logger


class Detector(Cron):
    def run_do(self):
        self.detect_running_task()
        self.detect_end_task()
        self.detect_running_job()
        self.detect_expired_session()

    @classmethod
    def detect_running_task(cls):
        detect_logger().info('start to detect running task..')
        count = 0
        try:
            running_tasks = JobSaver.query_task(party_status=TaskStatus.RUNNING)
            detect_logger().info(f'running task: {running_tasks}')
            stop_job_ids = set()
            for task in running_tasks:
                if task.f_run_ip != RuntimeConfig.JOB_SERVER_HOST:
                    cls.detect_cluster_instance_status(task, stop_job_ids)
                    continue
                count += 1
                try:
                    process_exist = build_engine(task.f_provider_name).is_alive(task)
                    if not process_exist:
                        msg = f"task {task.f_task_id} {task.f_task_version} on {task.f_role} {task.f_party_id}"
                        detect_logger(job_id=task.f_job_id).info(
                            f"{msg} with {task.f_party_status} process {task.f_run_pid} does not exist")
                        time.sleep(3)
                        _tasks = JobSaver.query_task(task_id=task.f_task_id, task_version=task.f_task_version,
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
                detect_logger().info('start to stop jobs: {}'.format(stop_job_ids))
            stop_jobs = set()
            for job_id in stop_job_ids:
                jobs = JobSaver.query_job(job_id=job_id)
                if jobs:
                    stop_jobs.add(jobs[0])
            cls.request_stop_jobs(jobs=stop_jobs, stop_msg="task executor process abort", stop_status=JobStatus.FAILED)
        except Exception as e:
            detect_logger().exception(e)
        finally:
            detect_logger().info(f"finish detect {count} running task")

    @classmethod
    def detect_end_task(cls):
        pass

    @classmethod
    def detect_running_job(cls):
        pass

    @classmethod
    def detect_expired_session(cls):
        pass

    @classmethod
    def request_stop_jobs(cls, jobs, stop_msg, stop_status):
        if not len(jobs):
            return
        detect_logger().info(f"have {len(jobs)} should be stopped, because of {stop_msg}")
        for job in jobs:
            try:
                detect_logger(job_id=job.f_job_id).info(
                    f"detector request start to stop job {job.f_job_id}, because of {stop_msg}")
                status = FederatedScheduler.request_stop_job(job_id=job.f_job_id, party_id=job.f_scheduler_party_id,
                                                             stop_status=stop_status)
                detect_logger(job_id=job.f_job_id).info(f"detector request stop job {job.f_job_id} {status}")
            except Exception as e:
                detect_logger(job_id=job.f_job_id).exception(e)

    @classmethod
    def detect_cluster_instance_status(cls, task, stop_job_ids):
        detect_logger(job_id=task.f_job_id).info('start detect running task instance status')
        try:
            latest_tasks = JobSaver.query_task(task_id=task.f_task_id, role=task.f_role, party_id=task.f_party_id)

            if len(latest_tasks) != 1:
                detect_logger(job_id=task.f_job_id).error(
                    f'query latest tasks of {task.f_task_id} failed, '
                    f'have {len(latest_tasks)} tasks'
                )
                return

            if task.f_task_version != latest_tasks[0].f_task_version:
                detect_logger(job_id=task.f_job_id).info(
                    f'{task.f_task_id} {task.f_task_version} is not the latest task, '
                     'update task status to failed'
                )
                JobSaver.update_task_status({
                    'task_id': task.f_task_id,
                    'role': task.f_role,
                    'party_id': task.f_party_id,
                    'task_version': task.f_task_version,
                    'status': JobStatus.FAILED,
                    'party_status': JobStatus.FAILED,
                })
                return

            instance_list = RuntimeConfig.SERVICE_DB.get_servers()
            instance_list = {instance.http_address for instance_id, instance in instance_list.items()}

            if f'{task.f_run_ip}:{task.f_run_port}' not in instance_list:
                detect_logger(job_id=task.f_job_id).error(
                     'detect cluster instance status failed, '
                     'add task {task.f_task_id} {task.f_task_version} to stop list'
                )
                stop_job_ids.add(task.f_job_id)
        except Exception as e:
            detect_logger(job_id=task.f_job_id).exception(e)


class FederatedDetector(Detector):
    def run_do(self):
        self.detect_running_job_federated()

    @classmethod
    def detect_running_job_federated(cls):
        pass
