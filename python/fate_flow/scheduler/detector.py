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

from fate_flow.controller.task import TaskController
from fate_flow.db import Task, Job
from fate_flow.db.base_models import DB
from fate_flow.engine.devices import build_engine
from fate_flow.engine.storage import Session
from fate_flow.entity.types import TaskStatus, JobStatus, EndStatus, LauncherType
from fate_flow.manager.operation.job_saver import JobSaver
from fate_flow.manager.service.resource_manager import ResourceManager
from fate_flow.runtime.runtime_config import RuntimeConfig
from fate_flow.controller.federated import FederatedScheduler
from fate_flow.runtime.system_settings import SESSION_VALID_PERIOD
from fate_flow.utils.base_utils import current_timestamp
from fate_flow.utils.cron import Cron
from fate_flow.utils.job_utils import check_task_is_timeout
from fate_flow.utils.log_utils import detect_logger


class Detector(Cron):
    def run_do(self):
        self.detect_running_task()
        self.detect_end_task()
        self.detect_resource_record()
        self.detect_expired_session()
        self.detect_deepspeed_task()

    @classmethod
    def detect_running_task(cls):
        detect_logger().info('start to detect running task..')
        count = 0
        try:
            running_tasks = JobSaver.query_task(party_status=TaskStatus.RUNNING)
            detect_logger().info(f'running task: {running_tasks}')
            stop_job_ids = set()
            for task in running_tasks:
                # check timeout
                if check_task_is_timeout(task):
                    stop_job_ids.add(task.f_job_id)
                    continue
                if task.f_run_ip != RuntimeConfig.JOB_SERVER_HOST:
                    cls.detect_cluster_instance_status(task, stop_job_ids)
                    continue
                count += 1
                try:
                    process_exist = build_engine(task.f_provider_name, task.f_launcher_name).is_alive(task)
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
                    if task.f_end_time and task.f_end_time - current_timestamp() < 5 * 60 * 1000:
                        continue
                    detect_logger().info(f'start to stop task {task.f_role} {task.f_party_id} {task.f_task_id}'
                                         f' {task.f_task_version}')
                    kill_task_status = TaskController.stop_task(task=task, stop_status=TaskStatus.FAILED)
                    detect_logger().info(f'kill task status: {kill_task_status}')
                    count += 1
                except Exception as e:
                    detect_logger().exception(e)
        except Exception as e:
            detect_logger().exception(e)
        finally:
            detect_logger().info(f"finish detect {count} end task")

    @classmethod
    def detect_expired_session(cls):
        ttl = SESSION_VALID_PERIOD
        detect_logger().info(f'start detect expired session by ttl {ttl/1000} s')
        try:
            session_records = Session.query_sessions(create_time=[None, current_timestamp() - ttl])
            for session_record in session_records:
                manager_session_id = session_record.f_manager_session_id
                if manager_session_id in RuntimeConfig.SESSION_LIST:
                    continue
                else:
                    RuntimeConfig.SESSION_LIST.append(manager_session_id)
                detect_logger().info(f'start destroy session {manager_session_id}')
                try:
                    sess = Session(session_id=manager_session_id, options={"logger": detect_logger()})
                    sess.destroy_all_sessions()
                except Exception as e:
                    detect_logger().error(f'stop session {manager_session_id} error', e)
                finally:
                    try:
                        RuntimeConfig.SESSION_LIST.remove(manager_session_id)
                    except:
                        pass
                    detect_logger().info(f'stop session {manager_session_id} successfully')
        except Exception as e:
            detect_logger().error('detect expired session error', e)
        finally:
            detect_logger().info('finish detect expired session')

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

    @classmethod
    def detect_deepspeed_task(cls):
        detect_logger().info('start to detect deepspeed running task..')
        running_tasks = JobSaver.query_task(party_status=TaskStatus.RUNNING, launcher_name=LauncherType.DEEPSPEED)
        for task in running_tasks:
            cls.detect_deepspeed_task_status(task)
        detect_logger().info(f'finish detect deepspeed running task {running_tasks}')

    @staticmethod
    def detect_deepspeed_task_status(task: Task):
        try:
            deepspeed_engine = build_engine(task.f_provider_name, task.f_launcher_name)
            # query or update
            if not deepspeed_engine.is_alive(task):
                # update task status to end status
                status = deepspeed_engine.query_task_status(task)
                detect_logger(task.f_job_id).info(f"task status: {status}")
                task_info = {
                    "job_id": task.f_job_id,
                    "task_id": task.f_task_id,
                    "task_version": task.f_task_version,
                    "role": task.f_role,
                    "party_id": task.f_party_id,
                    "party_status": status
                }
                TaskController.update_task_status(task_info)
                deepspeed_engine.download_log(task)
        except Exception as e:
            detect_logger(task.f_job_id).exception(e)

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


class FederatedDetector(Detector):
    def run_do(self):
        self.detect_running_job_federated()

    @classmethod
    def detect_running_job_federated(cls):
        pass
