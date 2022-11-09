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
from fate_arch.common import FederatedCommunicationType
from fate_flow.entity import RetCode
from fate_flow.entity.run_status import StatusSet, TaskStatus, EndStatus, AutoRerunStatus, InterruptStatus
from fate_flow.entity.run_status import FederatedSchedulingStatusCode
from fate_flow.entity.run_status import SchedulingStatusCode
from fate_flow.entity import RunParameters
from fate_flow.scheduler.client import SchedulerClient
from fate_flow.utils import job_utils
from fate_flow.scheduler.federated_scheduler import FederatedScheduler
from fate_flow.operation.job_saver import JobSaver
from fate_flow.utils.log_utils import schedule_logger
from fate_flow.manager.resource_manager import ResourceManager
from fate_flow.controller.job_controller import JobController
from fate_flow.db.db_models import Job, Task
from fate_flow.entity.types import TaskCleanResourceType


class TaskScheduler(object):
    @classmethod
    def schedule(cls, job, dsl_parser, canceled=False):
        schedule_logger(job.f_job_id).info("scheduling job tasks")
        tasks_group = JobSaver.get_tasks_asc(job_id=job.f_job_id)
        waiting_tasks = []
        auto_rerun_tasks = []
        job_interrupt = False
        for task in tasks_group.values():
            # todo: pull or push
            new_task_status = cls.get_federated_task_status(job_id=task.f_job_id, task_id=task.f_task_id, task_version=task.f_task_version)
            task_interrupt = False
            task_status_have_update = False
            if new_task_status != task.f_status:
                task_status_have_update = True
                schedule_logger(job.f_job_id).info(f"sync task status {task.f_status} to {new_task_status}")
                task.f_status = new_task_status
                FederatedScheduler.sync_task_status(task_id=task.f_task_id, status=task.f_status)
                JobSaver.update_task_status(task.to_human_model_dict(), is_scheduler=True, scheduler_status=True)
            if InterruptStatus.contains(new_task_status):
                task_interrupt = True
                job_interrupt = True
            if task.f_status == TaskStatus.WAITING:
                waiting_tasks.append(task)
            elif task_status_have_update and EndStatus.contains(task.f_status) or task_interrupt:
                command_body = {"is_asynchronous": True}
                schedule_logger(task.f_job_id).info(f"stop task body: {command_body}, task status: {task.f_status}")
                FederatedScheduler.stop_task(task_id=task.f_task_id, stop_status=task.f_status, command_body=command_body)
                if not canceled and AutoRerunStatus.contains(task.f_status):
                    # if task.f_auto_retries > 0:
                    #     auto_rerun_tasks.append(task)
                    #     schedule_logger(job.f_job_id).info(f"task {task.f_task_id} {task.f_status} will be retried")
                    # else:
                    # todo: auto retries
                    schedule_logger(job.f_job_id).info(f"task {task.f_task_id} {task.f_status} has no retry count")

        scheduling_status_code = SchedulingStatusCode.NO_NEXT
        schedule_logger(job.f_job_id).info(f"canceled status {canceled}, job interrupt status {job_interrupt}")
        if not canceled and not job_interrupt:
            for waiting_task in waiting_tasks:
                for component in dsl_parser.get_upstream_dependent_components(component_name=waiting_task.f_component_name):
                    dependent_task = tasks_group[job_utils.generate_task_id(job_id=job.f_job_id, component_name=component.get_name())]
                    if dependent_task.f_status != TaskStatus.SUCCESS:
                        # can not start task
                        break
                else:
                    # all upstream dependent tasks have been successful, can start this task
                    scheduling_status_code = SchedulingStatusCode.HAVE_NEXT
                    status_code = cls.start_task(job=job, task=waiting_task)
                    if status_code == SchedulingStatusCode.NO_RESOURCE:
                        # wait for the next round of scheduling
                        schedule_logger(job.f_job_id).info(f"task {waiting_task.f_task_id} can not apply resource, wait for the next round of scheduling")
                        break
                    elif status_code == SchedulingStatusCode.FAILED:
                        scheduling_status_code = SchedulingStatusCode.FAILED
                        waiting_task.f_status = StatusSet.FAILED
                        FederatedScheduler.sync_task_status(task_id=waiting_task.f_task_id, status=waiting_task.f_status)
                        break
        else:
            schedule_logger(job.f_job_id).info("have cancel signal, pass start job tasks")
        schedule_logger(job.f_job_id).info("finish scheduling job tasks")
        return scheduling_status_code, auto_rerun_tasks, tasks_group.values()

    @classmethod
    def start_task(cls, job, task):
        schedule_logger(task.f_job_id).info("try to start task {} {}".format(task.f_task_id, task.f_task_version))
        # todo: apply for task resource
        task.f_status = TaskStatus.RUNNING
        JobSaver.update_task_status(
            task_info=task.to_human_model_dict(only_primary_with=["status"]),
            is_scheduler=True,
            scheduler_status=True
        )
        schedule_logger(task.f_job_id).info("start task {} {}".format(task.f_task_id, task.f_task_version))
        FederatedScheduler.sync_task_status(task_id=task.f_task_id, status=task.f_status)
        JobSaver.update_task_status(task.to_human_model_dict(), is_scheduler=True, scheduler_status=True)
        status_code, response = FederatedScheduler.start_task(task_id=task.f_task_id)
        if status_code == FederatedSchedulingStatusCode.SUCCESS:
            return SchedulingStatusCode.SUCCESS
        else:
            return SchedulingStatusCode.FAILED

    @classmethod
    def prepare_rerun_task(cls, job: Job, task: Task, dsl_parser, auto=False, force=False):
        job_id = job.f_job_id
        can_rerun = False
        if force:
            can_rerun = True
            auto = False
            schedule_logger(job_id).info(f"task {task.f_task_id} {task.f_task_version} with {task.f_status} was forced to rerun")
        elif task.f_status in {TaskStatus.SUCCESS}:
            schedule_logger(job_id).info(f"task {task.f_task_id} {task.f_task_version} is {task.f_status} and not force reruen, pass rerun")
        elif auto and task.f_auto_retries < 1:
            schedule_logger(job_id).info(f"task {task.f_task_id} has no retry count, pass rerun")
        else:
            can_rerun = True
        if can_rerun:
            if task.f_status != TaskStatus.WAITING:
                cls.create_new_version_task(job=job,
                                            task=task,
                                            dsl_parser=dsl_parser,
                                            auto=auto)
        return can_rerun

    @classmethod
    def create_new_version_task(cls, job, task, dsl_parser, auto):
        # stop old version task
        FederatedScheduler.stop_task(task_id=task.f_task_id, stop_status=TaskStatus.CANCELED)
        FederatedScheduler.clean_task(task_id=task.f_task_id, content_type=TaskCleanResourceType.METRICS)
        # create new version task
        task.f_task_version = task.f_task_version + 1
        if auto:
            task.f_auto_retries = task.f_auto_retries - 1
        task.f_run_pid = None
        task.f_run_ip = None
        # todo: FederatedScheduler.create_task and JobController.initialize_tasks will create task twice
        status_code, response = FederatedScheduler.create_task(task_id=task.f_task_id, command_body=task.to_human_model_dict())
        if status_code != FederatedSchedulingStatusCode.SUCCESS:
            raise Exception(f"create {task.f_task_id} new version failed")
        # create the task holder in db to record information of all participants in the initiator for scheduling
        for _role in response:
            for _party_id in response[_role]:
                if _role == job.f_initiator_role and _party_id == job.f_initiator_party_id:
                    continue
                JobController.initialize_tasks(job_id=job.f_job_id,
                                               role=_role,
                                               party_id=_party_id,
                                               run_on_this_party=False,
                                               initiator_role=job.f_initiator_role,
                                               initiator_party_id=job.f_initiator_party_id,
                                               job_parameters=RunParameters(**job.f_runtime_conf_on_party["job_parameters"]),
                                               dsl_parser=dsl_parser,
                                               components=[task.f_component_name],
                                               task_version=task.f_task_version,
                                               auto_retries=task.f_auto_retries,
                                               runtime_conf=job.f_runtime_conf)
        schedule_logger(job.f_job_id).info(f"create task {task.f_task_id} new version {task.f_task_version} successfully")

    @classmethod
    def collect_task_of_all_party(cls, job, task, set_status=None):
        tasks_on_all_party = JobSaver.query_task(task_id=task.f_task_id, task_version=task.f_task_version,
                                                 party_task=True, is_scheduler=True)
        tasks_status_on_all = set([task.f_status for task in tasks_on_all_party])
        if not len(tasks_status_on_all) > 1 and TaskStatus.RUNNING not in tasks_status_on_all:
            return
        status, federated_response = FederatedScheduler.collect_task(task.f_task_id)
        if status != FederatedSchedulingStatusCode.SUCCESS:
            schedule_logger(job.f_job_id).warning(f"collect task {task.f_task_id} {task.f_task_version} failed")
        for _role in federated_response.keys():
            for _party_id, party_response in federated_response[_role].items():
                if party_response["retcode"] == RetCode.SUCCESS:
                    JobSaver.update_task_status(task_info=party_response["data"], is_scheduler=True)
                elif party_response["retcode"] == RetCode.FEDERATED_ERROR and set_status:
                    tmp_task_info = {
                        "job_id": task.f_job_id,
                        "task_id": task.f_task_id,
                        "task_version": task.f_task_version,
                        "role": _role,
                        "party_id": _party_id,
                        "party_status": TaskStatus.RUNNING
                    }
                    JobSaver.update_task_status(task_info=tmp_task_info, is_scheduler=True)

    @classmethod
    def get_federated_task_status(cls, job_id, task_id, task_version):
        tasks_on_all_party = JobSaver.query_task(task_id=task_id, task_version=task_version, party_task=True,
                                                 is_scheduler=True)
        status_flag = 0
        for task in tasks_on_all_party:
            if task.f_party_status != TaskStatus.SUCCESS:
                status_flag = 1
                break
        if status_flag:
            tasks_party_status = [task.f_party_status for task in tasks_on_all_party]
        else:
            tasks_party_status = [task.f_party_status for task in tasks_on_all_party]
        status = cls.calculate_multi_party_task_status(tasks_party_status)
        schedule_logger(job_id=job_id).info("task {} {} status is {}, calculate by task party status list: {}".format(task_id, task_version, status, tasks_party_status))
        return status

    @classmethod
    def calculate_multi_party_task_status(cls, tasks_party_status):
        # 1. all waiting
        # 2. have interrupt status, should be interrupted
        # 3. have running
        # 4. waiting + success/pass
        # 5. all the same end status
        tmp_status_set = set(tasks_party_status)
        if TaskStatus.PASS in tmp_status_set:
            tmp_status_set.remove(TaskStatus.PASS)
            tmp_status_set.add(TaskStatus.SUCCESS)
        if len(tmp_status_set) == 1:
            # 1 and 5
            return tmp_status_set.pop()
        else:
            # 2
            for status in sorted(InterruptStatus.status_list(), key=lambda s: StatusSet.get_level(status=s), reverse=True):
                if status in tmp_status_set:
                    return status
            # 3
            if TaskStatus.RUNNING in tmp_status_set:
                return TaskStatus.RUNNING
            # 4
            if TaskStatus.SUCCESS in tmp_status_set:
                return TaskStatus.RUNNING
            raise Exception("Calculate task status failed: {}".format(tasks_party_status))
