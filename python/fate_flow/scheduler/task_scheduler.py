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
from fate_flow.entity.dag_structures import DAGSchema
from fate_flow.entity.engine_types import FederatedCommunicationType
from fate_flow.entity.types import ReturnCode, ResourceOperation
from fate_flow.entity.run_status import StatusSet, TaskStatus, InterruptStatus, EndStatus, AutoRerunStatus, \
    SchedulingStatusCode
from fate_flow.entity.run_status import FederatedSchedulingStatusCode
from fate_flow.manager.resource_manager import ResourceManager
from fate_flow.scheduler.federated_scheduler import FederatedScheduler
from fate_flow.operation.job_saver import ScheduleJobSaver
from fate_flow.utils.log_utils import schedule_logger


class TaskScheduler(object):
    @classmethod
    def schedule(cls, job, job_parser, dag_schema: DAGSchema, canceled=False):
        schedule_logger(job.f_job_id).info("scheduling job tasks")
        tasks_group = ScheduleJobSaver.get_status_tasks_asc(job_id=job.f_job_id)
        waiting_tasks = {}
        auto_rerun_tasks = []
        job_interrupt = False
        for task in tasks_group.values():
            if dag_schema.dag.conf.federated_status_collect_type == FederatedCommunicationType.PULL:
                cls.collect_task_of_all_party(job=job, task=task)
            else:
                pass
            new_task_status = cls.get_federated_task_status(job_id=task.f_job_id, task_id=task.f_task_id,
                                                            task_version=task.f_task_version)
            task_interrupt = False
            task_status_have_update = False
            if new_task_status != task.f_status:
                task_status_have_update = True
                schedule_logger(job.f_job_id).info(f"sync task status {task.f_status} to {new_task_status}")
                task.f_status = new_task_status
                FederatedScheduler.sync_task_status(task_id=task.f_task_id, command_body={"status": task.f_status})
                ScheduleJobSaver.update_task_status(task.to_human_model_dict(),  scheduler_status=True)
            if InterruptStatus.contains(new_task_status):
                task_interrupt = True
                job_interrupt = True
            if task.f_status == TaskStatus.WAITING:
                waiting_tasks[task.f_task_name] = task
            elif task_status_have_update and EndStatus.contains(task.f_status) or task_interrupt:
                schedule_logger(task.f_job_id).info(f"stop task with status: {task.f_status}")
                FederatedScheduler.stop_task(task_id=task.f_task_id,  command_body={"status": task.f_status})
                if not canceled and AutoRerunStatus.contains(task.f_status):
                    if task.f_auto_retries > 0:
                        auto_rerun_tasks.append(task)
                        schedule_logger(job.f_job_id).info(f"task {task.f_task_id} {task.f_status} will be retried")
                    else:
                        schedule_logger(job.f_job_id).info(f"task {task.f_task_id} {task.f_status} has no retry count")

        scheduling_status_code = SchedulingStatusCode.NO_NEXT
        schedule_logger(job.f_job_id).info(f"canceled status {canceled}, job interrupt status {job_interrupt}")
        if not canceled and not job_interrupt:
            for task_id, waiting_task in waiting_tasks.items():
                dependent_tasks = job_parser.infer_dependent_tasks(
                    dag_schema.dag.tasks[waiting_task.f_task_name].inputs
                )
                schedule_logger(job.f_job_id).info(f"task {waiting_task.f_task_name} dependent tasks:{dependent_tasks}")
                for task_name in dependent_tasks:
                    dependent_task = tasks_group[task_name]
                    if dependent_task.f_status != TaskStatus.SUCCESS:
                        break
                else:
                    scheduling_status_code = SchedulingStatusCode.HAVE_NEXT
                    status_code = cls.start_task(job=job, task=waiting_task)
                    if status_code == SchedulingStatusCode.NO_RESOURCE:
                        schedule_logger(job.f_job_id).info(f"task {waiting_task.f_task_id} can not apply resource, wait for the next round of scheduling")
                        break
                    elif status_code == SchedulingStatusCode.FAILED:
                        schedule_logger(job.f_job_id).info(f"task status code: {status_code}")
                        scheduling_status_code = SchedulingStatusCode.FAILED
                        waiting_task.f_status = StatusSet.FAILED
                        FederatedScheduler.sync_task_status(task_id=waiting_task.f_task_id, command_body={
                            "status": waiting_task.f_status})
                        break
        else:
            schedule_logger(job.f_job_id).info("have cancel signal, pass start job tasks")
        schedule_logger(job.f_job_id).info("finish scheduling job tasks")
        return scheduling_status_code, auto_rerun_tasks, tasks_group.values()

    @classmethod
    def start_task(cls, job, task):
        schedule_logger(task.f_job_id).info("try to start task {} {}".format(task.f_task_id, task.f_task_version))
        # apply resource for task
        apply_status = cls.apply_task_resource(task, job)
        if not apply_status:
            return SchedulingStatusCode.NO_RESOURCE
        task.f_status = TaskStatus.RUNNING
        ScheduleJobSaver.update_task_status(
            task_info=task.to_human_model_dict(only_primary_with=["status"]), scheduler_status=True
        )
        schedule_logger(task.f_job_id).info("start task {} {}".format(task.f_task_id, task.f_task_version))
        FederatedScheduler.sync_task_status(task_id=task.f_task_id, command_body={"status": task.f_status})
        ScheduleJobSaver.update_task_status(task.to_human_model_dict(), scheduler_status=True)
        status_code, response = FederatedScheduler.start_task(task_id=task.f_task_id)
        if status_code == FederatedSchedulingStatusCode.SUCCESS:
            return SchedulingStatusCode.SUCCESS
        else:
            return SchedulingStatusCode.FAILED

    @classmethod
    def apply_task_resource(cls, task, job):
        apply_status_code, federated_response = FederatedScheduler.resource_for_task(
            task_id=task.f_task_id,
            operation_type=ResourceOperation.APPLY.value
        )
        if apply_status_code == FederatedSchedulingStatusCode.SUCCESS:
            return True
        else:
            # rollback resource
            rollback_party = []
            failed_party = []
            for dest_role in federated_response.keys():
                for dest_party_id in federated_response[dest_role].keys():
                    retcode = federated_response[dest_role][dest_party_id]["code"]
                    if retcode == ReturnCode.TASK.SUCCESS:
                        rollback_party.append({"role": dest_role, "party_id": [dest_party_id]})
                    else:
                        failed_party.append({"role": dest_role, "party_id": [dest_party_id]})
            schedule_logger(job.f_job_id).info("task apply resource failed on {}, rollback {}".format(failed_party,
                                                                                                      rollback_party))
            if rollback_party:
                return_status_code, federated_response = FederatedScheduler.resource_for_task(
                    task_id=task.f_task_id,
                    roles=rollback_party,
                    operation_type=ResourceOperation.RETURN.value
                )
                if return_status_code != FederatedSchedulingStatusCode.SUCCESS:
                    schedule_logger(job.f_job_id).info(f"task return resource failed:\n{federated_response}")
            else:
                schedule_logger(job.f_job_id).info("task no party should be rollback resource")
        return False

    @classmethod
    def collect_task_of_all_party(cls, job, task, set_status=None):
        tasks_on_all_party = ScheduleJobSaver.query_task(task_id=task.f_task_id, task_version=task.f_task_version)
        tasks_status_on_all = set([task.f_status for task in tasks_on_all_party])
        if not len(tasks_status_on_all) > 1 and TaskStatus.RUNNING not in tasks_status_on_all:
            return
        status, federated_response = FederatedScheduler.collect_task(task_id=task.f_task_id)
        if status != FederatedSchedulingStatusCode.SUCCESS:
            schedule_logger(job.f_job_id).warning(f"collect task {task.f_task_id} {task.f_task_version} failed")
        for _role in federated_response.keys():
            for _party_id, party_response in federated_response[_role].items():
                if party_response["code"] == ReturnCode.TASK.SUCCESS:
                    ScheduleJobSaver.update_task_status(task_info=party_response["data"])
                elif set_status:
                    tmp_task_info = {
                        "job_id": task.f_job_id,
                        "task_id": task.f_task_id,
                        "task_version": task.f_task_version,
                        "role": _role,
                        "party_id": _party_id,
                        "party_status": set_status
                    }
                    ScheduleJobSaver.update_task_status(task_info=tmp_task_info)

    @classmethod
    def get_federated_task_status(cls, job_id, task_id, task_version):
        tasks_on_all_party = ScheduleJobSaver.query_task(task_id=task_id, task_version=task_version)
        tasks_party_status = [task.f_status for task in tasks_on_all_party]
        status = cls.calculate_multi_party_task_status(tasks_party_status)
        schedule_logger(job_id=job_id).info("task {} {} status is {}, calculate by task party status list: {}".format(task_id, task_version, status, tasks_party_status))
        return status

    @classmethod
    def calculate_multi_party_task_status(cls, tasks_party_status):
        tmp_status_set = set(tasks_party_status)
        if TaskStatus.PASS in tmp_status_set:
            tmp_status_set.remove(TaskStatus.PASS)
            tmp_status_set.add(TaskStatus.SUCCESS)
        if len(tmp_status_set) == 1:
            return tmp_status_set.pop()
        else:
            for status in sorted(InterruptStatus.status_list(), key=lambda s: StatusSet.get_level(status=s), reverse=True):
                if status in tmp_status_set:
                    return status
            if TaskStatus.RUNNING in tmp_status_set:
                return TaskStatus.RUNNING
            if TaskStatus.SUCCESS in tmp_status_set:
                return TaskStatus.RUNNING
            raise Exception("Calculate task status failed: {}".format(tasks_party_status))
