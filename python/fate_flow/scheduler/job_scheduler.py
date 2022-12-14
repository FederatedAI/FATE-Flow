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
from fate_flow.scheduler.task_scheduler import TaskScheduler
from fate_flow.controller.job_controller import JobController
from fate_flow.db.base_models import DB
from fate_flow.db.schedule_models import ScheduleJob
from fate_flow.entity import RetCode
from fate_flow.entity.dag_structures import DAGSchema
from fate_flow.entity.run_status import StatusSet, FederatedSchedulingStatusCode, JobStatus, TaskStatus, EndStatus, \
    SchedulingStatusCode, InterruptStatus
from fate_flow.entity.types import ResourceOperation
from fate_flow.operation.job_saver import ScheduleJobSaver
from fate_flow.runtime.job_default_config import JobDefaultConfig
from fate_flow.scheduler.dsl_parser import DagParser
from fate_flow.scheduler.federated_scheduler import FederatedScheduler
from fate_flow.utils import job_utils, schedule_utils
from fate_flow.utils.base_utils import current_timestamp, json_dumps
from fate_flow.utils.cron import Cron
from fate_flow.utils.log_utils import schedule_logger, exception_to_trace_string


class DAGScheduler(Cron):
    @classmethod
    def submit(cls, dag_schema: DAGSchema):
        job_id = job_utils.generate_job_id()
        schedule_logger(job_id).info(f"submit job, dag {dag_schema.dag.to_dict()}, schema version {dag_schema.schema_version}")
        submit_result = {
            "job_id": job_id
        }
        try:
            job = ScheduleJob()
            job.f_job_id = job_id
            job.f_dag = dag_schema.dict()
            job.f_parties = [party.dict() for party in dag_schema.dag.parties]
            job.f_initiator_party_id = dag_schema.dag.conf.initiator_party_id
            job.f_scheduler_party_id = dag_schema.dag.conf.scheduler_party_id
            auto_retries = 0
            if not dag_schema.dag.conf.federated_status_collect_type:
                dag_schema.dag.conf.federated_status_collect_type = "PUSH"
            job.f_status = StatusSet.READY
            ScheduleJobSaver.create_job(job.to_human_model_dict())
            status_code, response = FederatedScheduler.create_job(
                job_id, job.f_parties, {"dag_schema": dag_schema.dict(), "job_id": job_id}
            )
            if status_code != FederatedSchedulingStatusCode.SUCCESS:
                job.f_status = JobStatus.FAILED
                FederatedScheduler.sync_job_status(job_id=job.f_job_id, roles=job.f_parties, job_info={
                    "job_id": job.f_job_id,
                    "status": job.f_status
                })
                raise Exception("create job failed", response)
            else:
                job.f_status = JobStatus.WAITING
                cls.create_schedule_tasks(job, dag_schema)
                status_code, response = FederatedScheduler.sync_job_status(job_id=job.f_job_id, roles=job.f_parties,
                                                                           job_info={"job_id": job.f_job_id,
                                                                                     "status": job.f_status})
                if status_code != FederatedSchedulingStatusCode.SUCCESS:
                    raise Exception(f"set job to waiting status failed: {response}")
                ScheduleJobSaver.update_job_status({"job_id": job.f_job_id, "status": job.f_status})
            schedule_logger(job_id).info(f"submit job successfully, job id is {job.f_job_id}")
            result = {
                "code": RetCode.SUCCESS,
                "message": "success"
            }
            submit_result.update(result)
        except Exception as e:
            schedule_logger(job_id).exception(e)
            submit_result["code"] = RetCode.OPERATING_ERROR
            submit_result["message"] = exception_to_trace_string(e)
        return submit_result

    @staticmethod
    def create_schedule_tasks(job: ScheduleJob, dag_schema):
        for party in job.f_parties:
            role = party.get("role")
            party_ids = party.get("party_id")
            for party_id in party_ids:
                JobController.create_tasks(job.f_job_id, role, party_id, dag_schema, is_scheduler=True)
        JobController.create_scheduler_tasks_status(job.f_job_id, dag_schema)

    def run_do(self):
        # waiting
        schedule_logger().info("start schedule waiting jobs")
        jobs = ScheduleJobSaver.query_job(status=JobStatus.WAITING, order_by="create_time", reverse=False)
        schedule_logger().info(f"have {len(jobs)} waiting jobs")
        if len(jobs):
            job = jobs[0]
            schedule_logger().info(f"schedule waiting job {job.f_job_id}")
            try:
                self.schedule_waiting_jobs(job=job)
            except Exception as e:
                schedule_logger(job.f_job_id).exception(e)
                schedule_logger(job.f_job_id).error("schedule waiting job failed")
        schedule_logger().info("schedule waiting jobs finished")

        # running
        schedule_logger().info("start schedule running jobs")
        jobs = ScheduleJobSaver.query_job(status=JobStatus.RUNNING, order_by="create_time", reverse=False)
        schedule_logger().info(f"have {len(jobs)} running jobs")
        for job in jobs:
            schedule_logger().info(f"schedule running job {job.f_job_id}")
            try:
                self.schedule_running_job(job=job)
            except Exception as e:
                schedule_logger(job.f_job_id).exception(e)
                schedule_logger(job.f_job_id).error("schedule job failed")
        schedule_logger().info("schedule running jobs finished")

        # ready
        schedule_logger().info("start schedule ready jobs")
        jobs = ScheduleJobSaver.query_job(ready_signal=True, order_by="create_time", reverse=False)
        schedule_logger().info(f"have {len(jobs)} ready jobs")
        for job in jobs:
            schedule_logger().info(f"schedule ready job {job.f_job_id}")
            try:
                pass
            except Exception as e:
                schedule_logger(job.f_job_id).exception(e)
                schedule_logger(job.f_job_id).error(f"schedule ready job failed:\n{e}")
        schedule_logger().info("schedule ready jobs finished")

        schedule_logger().info("start schedule rerun jobs")

        # rerun
        # todo:

        # end
        schedule_logger().info("start schedule end status jobs to update status")
        jobs = ScheduleJobSaver.query_job(status=set(EndStatus.status_list()),
                                          end_time=[current_timestamp() - JobDefaultConfig.end_status_job_scheduling_time_limit,
                                                    current_timestamp()])
        schedule_logger().info(f"have {len(jobs)} end status jobs")
        for job in jobs:
            schedule_logger().info(f"schedule end status job {job.f_job_id}")
            try:
                update_status = self.end_scheduling_updates(job_id=job.f_job_id)
                if update_status:
                    schedule_logger(job.f_job_id).info("try update status by scheduling like running job")
                else:
                    schedule_logger(job.f_job_id).info("the number of updates has been exceeded")
                    continue
                self.schedule_running_job(job=job, force_sync_status=True)
            except Exception as e:
                schedule_logger(job.f_job_id).exception(e)
                schedule_logger(job.f_job_id).error("schedule job failed")
        schedule_logger().info("schedule end status jobs finished")

    @classmethod
    def schedule_waiting_jobs(cls, job: ScheduleJob):
        job_id = job.f_job_id
        if job.f_cancel_signal:
            FederatedScheduler.sync_job_status(job_id=job.f_job_id, roles=job.f_parties,
                                               job_info={"job_id": job.f_job_id, "status": JobStatus.CANCELED})
            ScheduleJobSaver.update_job_status({"job_id": job.f_job_id, "status": JobStatus.CANCELED})
            schedule_logger(job.job_id).info("job have cancel signal")
            return
        apply_status_code, federated_response = FederatedScheduler.resource_for_job(
            job_id=job.f_job_id,
            roles=job.f_parties,
            operation_type=ResourceOperation.APPLY.value
        )
        if apply_status_code == FederatedSchedulingStatusCode.SUCCESS:
            cls.start_job(job_id=job_id, roles=job.f_parties)
        else:
            # rollback resource
            rollback_party = []
            failed_party = []
            for dest_role in federated_response.keys():
                for dest_party_id in federated_response[dest_role].keys():
                    retcode = federated_response[dest_role][dest_party_id]["retcode"]
                    if retcode == 0:
                        rollback_party.append({"role": dest_role, "party_id": dest_party_id})
                    else:
                        failed_party.append({"role": dest_role, "party_id": dest_party_id})
            schedule_logger(job_id).info("job apply resource failed on {}, rollback {}".format(failed_party,
                                                                                               rollback_party))
            if rollback_party:
                return_status_code, federated_response = FederatedScheduler.resource_for_job(
                    job_id=job_id,
                    roles=rollback_party,
                    operation_type=ResourceOperation.RETURN.value
                )
                if return_status_code != FederatedSchedulingStatusCode.SUCCESS:
                    schedule_logger(job_id).info(f"job return resource failed:\n{federated_response}")
            else:
                schedule_logger(job_id).info("job no party should be rollback resource")
            if apply_status_code == FederatedSchedulingStatusCode.ERROR:
                cls.stop_job(job_id=job_id, stop_status=JobStatus.FAILED)
                schedule_logger(job_id).info("apply resource error, stop job")

    def schedule_running_job(cls, job: ScheduleJob, force_sync_status=False):
        schedule_logger(job.f_job_id).info("scheduling running job")
        dag_parser = DagParser()
        dag_parser.parse_dag(dag_schema=DAGSchema(**job.f_dag))
        task_scheduling_status_code, auto_rerun_tasks, tasks = TaskScheduler.schedule(job=job, dag_parser=dag_parser,
                                                                                      canceled=job.f_cancel_signal,
                                                                                      dag_schema=DAGSchema(**job.f_dag))

        tasks_status = dict([(task.f_task_name, task.f_status) for task in tasks])
        schedule_logger(job_id=job.f_job_id).info(f"task_scheduling_status_code: {task_scheduling_status_code}, "
                                                  f"tasks_status: {tasks_status.values()}")
        new_job_status = cls.calculate_job_status(task_scheduling_status_code=task_scheduling_status_code, tasks_status=tasks_status.values())
        if new_job_status == JobStatus.WAITING and job.f_cancel_signal:
            new_job_status = JobStatus.CANCELED
        total, finished_count = cls.calculate_job_progress(tasks_status=tasks_status)
        new_progress = float(finished_count) / total * 100
        schedule_logger(job.f_job_id).info(f"job status is {new_job_status}, calculate by task status list: {tasks_status}")
        if new_job_status != job.f_status or new_progress != job.f_progress:
            # Make sure to update separately, because these two fields update with anti-weight logic
            if int(new_progress) - job.f_progress > 0:
                job.f_progress = new_progress
                FederatedScheduler.update_job(job_id=job.f_job_id,
                                              roles=job.f_parties,
                                              command_body={"job_id": job.f_job_id, "progress": job.f_progress})
                cls.update_job_on_scheduler(schedule_job=job, update_fields=["progress"])
            if new_job_status != job.f_status:
                job.f_status = new_job_status
                if EndStatus.contains(job.f_status):
                    FederatedScheduler.save_pipelined_model(job_id=job.f_job_id, roles=job.f_parties)
                FederatedScheduler.sync_job_status(job_id=job.f_job_id, roles=job.f_parties,
                                                   job_info={"job_id": job.f_job_id,
                                                             "status": job.f_status})
                cls.update_job_on_scheduler(schedule_job=job, update_fields=["status"])
        if EndStatus.contains(job.f_status):
            cls.finish(job=job, end_status=job.f_status)
        if auto_rerun_tasks:
            schedule_logger(job.f_job_id).info("job have auto rerun tasks")
        if force_sync_status:
            FederatedScheduler.sync_job_status(job_id=job.f_job_id, roles=job.f_roles, status=job.f_status,
                                               job_info=job.to_human_model_dict())
        schedule_logger(job.f_job_id).info("finish scheduling running job")

    @classmethod
    def calculate_job_status(cls, task_scheduling_status_code, tasks_status):
        tmp_status_set = set(tasks_status)
        if TaskStatus.PASS in tmp_status_set:
            tmp_status_set.remove(TaskStatus.PASS)
            tmp_status_set.add(TaskStatus.SUCCESS)
        if len(tmp_status_set) == 1:
            return tmp_status_set.pop()
        else:
            if TaskStatus.RUNNING in tmp_status_set:
                return JobStatus.RUNNING
            if TaskStatus.WAITING in tmp_status_set:
                if task_scheduling_status_code == SchedulingStatusCode.HAVE_NEXT:
                    return JobStatus.RUNNING
                else:
                    pass
            for status in sorted(InterruptStatus.status_list(), key=lambda s: StatusSet.get_level(status=s), reverse=True):
                if status in tmp_status_set:
                    return status
            if tmp_status_set == {TaskStatus.WAITING, TaskStatus.SUCCESS} and task_scheduling_status_code == SchedulingStatusCode.NO_NEXT:
                return JobStatus.CANCELED

            raise Exception("calculate job status failed, all task status: {}".format(tasks_status))

    @classmethod
    def calculate_job_progress(cls, tasks_status):
        total = 0
        finished_count = 0
        for task_status in tasks_status.values():
            total += 1
            if EndStatus.contains(task_status):
                finished_count += 1
        return total, finished_count

    @classmethod
    def start_job(cls, job_id, roles):
        schedule_logger(job_id).info(f"start job {job_id}")
        status_code, response = FederatedScheduler.start_job(job_id, roles)
        schedule_logger(job_id).info(f"start job {job_id} status code: {status_code}, response: {response}")
        ScheduleJobSaver.update_job_status(job_info={"job_id": job_id, "status": StatusSet.RUNNING})

    @classmethod
    def stop_job(cls, job_id, stop_status):
        schedule_logger(job_id).info(f"request stop job with {stop_status}")
        jobs = ScheduleJobSaver.query_job(job_id=job_id)
        if len(jobs) > 0:
            if stop_status == JobStatus.CANCELED:
                schedule_logger(job_id).info("cancel job")
                set_cancel_status = schedule_utils.cancel_signal(job_id=job_id, set_or_reset=True)
                schedule_logger(job_id).info(f"set job cancel signal {set_cancel_status}")
            job = jobs[0]
            job.f_status = stop_status
            schedule_logger(job_id).info(f"request stop job with {stop_status} to all party")
            status_code, response = FederatedScheduler.stop_job(job_id=job_id, roles=job.f_parties)
            if status_code == FederatedSchedulingStatusCode.SUCCESS:
                schedule_logger(job_id).info(f"stop job with {stop_status} successfully")
                return RetCode.SUCCESS, "success"
            else:
                tasks_group = ScheduleJobSaver.get_status_tasks_asc(job_id=job.f_job_id)
                for task in tasks_group.values():
                    TaskScheduler.collect_task_of_all_party(job, task=task, set_status=stop_status)
                schedule_logger(job_id).info(f"stop job with {stop_status} failed, {response}")
                return RetCode.FEDERATED_ERROR, json_dumps(response)
        else:
            return RetCode.SUCCESS, "can not found job"

    @classmethod
    @DB.connection_context()
    def end_scheduling_updates(cls, job_id):
        operate = ScheduleJob.update({
            ScheduleJob.f_end_scheduling_updates: ScheduleJob.f_end_scheduling_updates + 1}
        ).where(
            ScheduleJob.f_job_id == job_id,
            ScheduleJob.f_end_scheduling_updates < JobDefaultConfig.end_status_job_scheduling_updates
        )
        update_status = operate.execute() > 0
        return update_status

    @classmethod
    def update_job_on_scheduler(cls, schedule_job: ScheduleJob, update_fields: list):
        schedule_logger(schedule_job.f_job_id).info(f"try to update job {update_fields} on scheduler")
        jobs = ScheduleJobSaver.query_job(job_id=schedule_job.f_job_id)
        if not jobs:
            raise Exception("Failed to update job status on scheduler")
        job_info = schedule_job.to_human_model_dict(only_primary_with=update_fields)
        for field in update_fields:
            job_info[field] = getattr(schedule_job, "f_%s" % field)
        ScheduleJobSaver.update_job_status(job_info=job_info)
        ScheduleJobSaver.update_job(job_info=job_info)
        schedule_logger(schedule_job.f_job_id).info(f"update job {update_fields} on scheduler finished")

    @classmethod
    def finish(cls, job, end_status):
        schedule_logger(job.f_job_id).info(f"job finished with {end_status}, do something...")
        cls.stop_job(job_id=job.f_job_id, stop_status=end_status)
        # todo: clean job
        schedule_logger(job.f_job_id).info(f"job finished with {end_status}, done")