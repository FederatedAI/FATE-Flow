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
from typing import List

from fate_arch.common.base_utils import current_timestamp
from fate_arch.session import Session

from fate_flow.controller.engine_adapt import build_engine
from fate_flow.controller.job_controller import JobController
from fate_flow.controller.task_controller import TaskController
from fate_flow.db.db_models import DB, DependenciesStorageMeta, Job
from fate_flow.db.job_default_config import JobDefaultConfig
from fate_flow.db.runtime_config import RuntimeConfig
from fate_flow.entity.run_status import (
    EndStatus, FederatedSchedulingStatusCode,
    JobStatus, TaskStatus,
)
from fate_flow.manager.dependence_manager import DependenceManager
from fate_flow.manager.resource_manager import ResourceManager
from fate_flow.operation.job_saver import JobSaver
from fate_flow.scheduler.federated_scheduler import FederatedScheduler
from fate_flow.settings import SESSION_VALID_PERIOD
from fate_flow.utils.api_utils import is_localhost
from fate_flow.utils.cron import Cron
from fate_flow.utils.job_utils import check_job_is_timeout, generate_retry_interval
from fate_flow.utils.process_utils import check_process
from fate_flow.utils.log_utils import detect_logger


class Detector(Cron):
    def run_do(self):
        self.detect_running_task()
        self.detect_end_task()
        self.detect_running_job()
        self.detect_resource_record()
        self.detect_expired_session()
        self.detect_dependence_upload_record()

    @classmethod
    def detect_running_task(cls):
        detect_logger().info('start to detect running task..')
        count = 0
        try:
            running_tasks = JobSaver.query_task(party_status=TaskStatus.RUNNING, run_on_this_party=True)
            stop_job_ids = set()
            for task in running_tasks:
                if task.f_run_ip != RuntimeConfig.JOB_SERVER_HOST:
                    cls.detect_cluster_instance_status(task, stop_job_ids)
                    continue
                if not task.f_engine_conf or task.f_run_ip != RuntimeConfig.JOB_SERVER_HOST:
                    continue
                count += 1
                try:
                    process_exist = build_engine(task.f_engine_conf.get("computing_engine")).is_alive(task)
                    if not process_exist:
                        msg = f"task {task.f_task_id} {task.f_task_version} on {task.f_role} {task.f_party_id}"
                        detect_logger(job_id=task.f_job_id).info(f"{msg} with {task.f_party_status} process {task.f_run_pid} does not exist")
                        time.sleep(3)
                        _tasks = JobSaver.query_task(task_id=task.f_task_id, task_version=task.f_task_version, role=task.f_role, party_id=task.f_party_id)
                        if _tasks:
                            if _tasks[0].f_party_status == TaskStatus.RUNNING:
                                stop_job_ids.add(task.f_job_id)
                                detect_logger(job_id=task.f_job_id).info(f"{msg} party status has been checked twice, try to stop job")
                            else:
                                detect_logger(job_id=task.f_job_id).info(f"{msg} party status has changed to {_tasks[0].f_party_status}, may be stopped by task_controller.stop_task, pass stop job again")
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
        detect_logger().info('start to detect end status task..')
        count = 0
        try:
            tasks = JobSaver.query_task(
                run_ip=RuntimeConfig.JOB_SERVER_HOST,
                run_port=RuntimeConfig.HTTP_PORT,
                status=set(EndStatus.status_list()),
                kill_status=False
            )
            for task in tasks:
                try:
                    if task.f_end_time and task.f_end_time -  current_timestamp() < 5 * 60 * 1000:
                        continue
                    detect_logger().info(f'start to stop task {task.f_role} {task.f_party_id} {task.f_task_id}'
                                         f' {task.f_task_version}')
                    kill_task_status = TaskController.stop_task(task=task, stop_status=TaskStatus.FAILED)
                    detect_logger().info( f'kill task status: {kill_task_status}')
                    count += 1
                except Exception as e:
                    detect_logger().exception(e)
        except Exception as e:
            detect_logger().exception(e)
        finally:
            detect_logger().info(f"finish detect {count} end task")

    @classmethod
    def detect_running_job(cls):
        detect_logger().info('start detect running job')
        try:
            running_jobs = JobSaver.query_job(status=JobStatus.RUNNING, is_initiator=True)
            stop_jobs = set()
            for job in running_jobs:
                try:
                    if check_job_is_timeout(job):
                        stop_jobs.add(job)
                except Exception as e:
                    detect_logger(job_id=job.f_job_id).exception(e)
            cls.request_stop_jobs(jobs=stop_jobs, stop_msg="running timeout", stop_status=JobStatus.TIMEOUT)
        except Exception as e:
            detect_logger().exception(e)
        finally:
            detect_logger().info('finish detect running job')

    @classmethod
    @DB.connection_context()
    def detect_resource_record(cls):
        detect_logger().info('start detect resource recycle')
        try:
            filter_status = EndStatus.status_list()
            filter_status.append(JobStatus.WAITING)
            jobs = Job.select().where(Job.f_resource_in_use == True, current_timestamp() - Job.f_apply_resource_time > 10 * 60 * 1000, Job.f_status << filter_status)
            stop_jobs = set()
            for job in jobs:
                if job.f_status == JobStatus.WAITING:
                    stop_jobs.add(job)
                else:
                    try:
                        detect_logger(job_id=job.f_job_id).info(f"start to return job {job.f_job_id} on {job.f_role} {job.f_party_id} resource")
                        flag = ResourceManager.return_job_resource(job_id=job.f_job_id, role=job.f_role, party_id=job.f_party_id)
                        if flag:
                            detect_logger(job_id=job.f_job_id).info(f"return job {job.f_job_id} on {job.f_role} {job.f_party_id} resource successfully")
                        else:
                            detect_logger(job_id=job.f_job_id).info(f"return job {job.f_job_id} on {job.f_role} {job.f_party_id} resource failed")
                    except Exception as e:
                        detect_logger(job_id=job.f_job_id).exception(e)
            cls.request_stop_jobs(jobs=stop_jobs, stop_msg="start timeout", stop_status=JobStatus.TIMEOUT)
        except Exception as e:
            detect_logger().exception(e)
        finally:
            detect_logger().info('finish detect resource recycle')

    @classmethod
    @DB.connection_context()
    def detect_dependence_upload_record(cls):
        detect_logger().info('start detect dependence upload process')
        try:
            upload_process_list = DependenciesStorageMeta.select().where(DependenciesStorageMeta.f_upload_status==True)
            for dependence in upload_process_list:
                if int(dependence.f_pid):
                    is_alive = check_process(pid=int(dependence.f_pid))
                    if not is_alive:
                        try:
                            DependenceManager.kill_upload_process(version=dependence.f_version,
                                                                  storage_engine=dependence.f_storage_engine,
                                                                  dependence_type=dependence.f_type)
                        except Exception as e:
                            detect_logger().exception(e)
        except Exception as e:
            detect_logger().exception(e)
        finally:
            detect_logger().info('finish detect dependence upload process')

    @classmethod
    def detect_expired_session(cls):
        ttl = SESSION_VALID_PERIOD
        detect_logger().info(f'start detect expired session by ttl {ttl/1000} s')
        try:
            session_records = Session.query_sessions(create_time=[None, current_timestamp() - ttl])
            manager_session_id_list = []
            for session_record in session_records:
                manager_session_id = session_record.f_manager_session_id
                if manager_session_id in manager_session_id_list:
                    continue
                manager_session_id_list.append(manager_session_id)
                detect_logger().info(f'start destroy session {manager_session_id}')
                try:
                    sess = Session(session_id=manager_session_id, options={"logger": detect_logger()})
                    sess.destroy_all_sessions()
                except Exception as e:
                    detect_logger().error(f'stop session {manager_session_id} error', e)
                finally:
                    detect_logger().info(f'stop session {manager_session_id} successfully')
        except Exception as e:
            detect_logger().error('detect expired session error', e)
        finally:
            detect_logger().info('finish detect expired session')

    @classmethod
    def request_stop_jobs(cls, jobs: List[Job], stop_msg, stop_status):
        if not len(jobs):
            return
        detect_logger().info(f"have {len(jobs)} should be stopped, because of {stop_msg}")
        for job in jobs:
            try:
                detect_logger(job_id=job.f_job_id).info(f"detector request start to stop job {job.f_job_id}, because of {stop_msg}")
                status = FederatedScheduler.request_stop_job(job=job, stop_status=stop_status)
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

            if not task.f_run_ip or not task.f_run_port or is_localhost(task.f_run_ip):
                return

            instance_list = RuntimeConfig.SERVICE_DB.get_servers()
            instance_list = {instance.http_address for instance_id, instance in instance_list.items()}

            if f'{task.f_run_ip}:{task.f_run_port}' not in instance_list:
                detect_logger(job_id=task.f_job_id).warning(
                     'detect cluster instance status failed, '
                    f'add task {task.f_task_id} {task.f_task_version} to stop list'
                )
                stop_job_ids.add(task.f_job_id)
        except Exception as e:
            detect_logger(job_id=task.f_job_id).exception(e)


class FederatedDetector(Detector):
    def run_do(self):
        self.detect_running_job_federated()

    @classmethod
    def detect_running_job_federated(cls):
        detect_logger().info('start federated detect running job')
        try:
            running_jobs = JobSaver.query_job(status=JobStatus.RUNNING)
            stop_jobs = set()
            for job in running_jobs:
                cur_retry = 0
                max_retry_cnt = JobDefaultConfig.detect_connect_max_retry_count
                long_retry_cnt = JobDefaultConfig.detect_connect_long_retry_count
                exception = None
                while cur_retry < max_retry_cnt:
                    detect_logger().info(f"start federated detect running job {job.f_job_id} cur_retry={cur_retry}")
                    try:
                        status_code, response = FederatedScheduler.connect(job)
                        if status_code != FederatedSchedulingStatusCode.SUCCESS:
                            exception = f"connect code: {status_code}"
                        else:
                            exception = None
                            detect_logger().info(f"federated detect running job {job.f_job_id} success")
                            break
                    except Exception as e:
                        exception = e
                        detect_logger(job_id=job.f_job_id).debug(e)
                    finally:
                        retry_interval = generate_retry_interval(cur_retry, max_retry_cnt, long_retry_cnt)
                        time.sleep(retry_interval)
                        cur_retry += 1
                if exception is not None:
                    try:
                        JobController.stop_jobs(job_id=job.f_job_id, stop_status=JobStatus.FAILED)
                    except exception as e:
                        detect_logger().exception(f"stop job failed: {e}")
                    detect_logger(job.f_job_id).info(f"job {job.f_job_id} connect failed: {exception}")
                    stop_jobs.add(job)
            cls.request_stop_jobs(jobs=stop_jobs, stop_msg="federated error", stop_status=JobStatus.FAILED)
        except Exception as e:
            detect_logger().exception(e)
        finally:
            detect_logger().info('finish federated detect running job')
