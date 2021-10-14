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

from fate_arch.common.base_utils import current_timestamp
from fate_flow.controller.engine_adapt import build_engine
from fate_flow.db.db_models import DB, Job, DependenciesStorageMeta
from fate_arch.session import Session
from fate_flow.utils.log_utils import detect_logger
from fate_flow.manager.dependence_manager import DependenceManager
from fate_flow.scheduler.federated_scheduler import FederatedScheduler
from fate_flow.entity.run_status import JobStatus, TaskStatus, EndStatus
from fate_flow.settings import SESSION_VALID_PERIOD
from fate_flow.utils import cron, job_utils, process_utils
from fate_flow.db.runtime_config import RuntimeConfig
from fate_flow.operation.job_saver import JobSaver
from fate_flow.manager.resource_manager import ResourceManager
from fate_arch.common import EngineType


class Detector(cron.Cron):
    def run_do(self):
        self.detect_running_task()
        self.detect_running_job()
        self.detect_resource_record()
        self.detect_expired_session()
        self.detect_dependence_upload_record()

    @classmethod
    def detect_running_task(cls):
        detect_logger().info('start to detect running task..')
        count = 0
        try:
            running_tasks = JobSaver.query_task(party_status=TaskStatus.RUNNING, only_latest=False)
            stop_job_ids = set()
            for task in running_tasks:
                if not task.f_engine_conf and task.f_run_ip != RuntimeConfig.JOB_SERVER_HOST and not task.f_run_on_this_party:
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
                                detect_logger(task.f_job_id).info(f"{msg} party status has been checked twice, try to stop job")
                            else:
                                detect_logger(task.f_job_id).info(f"{msg} party status has changed to {_tasks[0].f_party_status}, may be stopped by task_controller.stop_task, pass stop job again")
                        else:
                            detect_logger(task.f_job_id).warning(f"{msg} can not found on db")
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
    def detect_running_job(cls):
        detect_logger().info('start detect running job')
        try:
            running_jobs = JobSaver.query_job(status=JobStatus.RUNNING, is_initiator=True)
            stop_jobs = set()
            for job in running_jobs:
                try:
                    if job_utils.check_job_is_timeout(job):
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
                    is_alive = process_utils.check_process(pid=int(dependence.f_pid))
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
                if manager_session_id not in manager_session_id:
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
    def request_stop_jobs(cls, jobs: [Job], stop_msg, stop_status):
        if not len(jobs):
            return
        detect_logger().info(f"have {len(jobs)} should be stopped, because of {stop_msg}")
        for job in jobs:
            try:
                detect_logger(job_id=job.f_job_id).info(f"detector request start to stop job {job.f_job_id}, because of {stop_msg}")
                FederatedScheduler.request_stop_job(job=job, stop_status=stop_status)
                detect_logger(job_id=job.f_job_id).info(f"detector request stop job {job.f_job_id} successfully")
            except Exception as e:
                detect_logger(job_id=job.f_job_id).exception(e)
