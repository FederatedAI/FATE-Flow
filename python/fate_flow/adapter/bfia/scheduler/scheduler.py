from fate_flow.adapter.bfia.utils.entity.code import ReturnCode
from fate_flow.adapter.bfia.utils.entity.status import StatusSet, TaskStatus, JobStatus, InterruptStatus, EndStatus
from fate_flow.adapter.bfia.wheels.federated import BfiaFederatedScheduler
from fate_flow.adapter.bfia.wheels.job import BfiaJobController
from fate_flow.adapter.bfia.utils.spec.job import DagSchemaSpec
from fate_flow.adapter.bfia.wheels.parser import get_dag_parser, translate_bfia_dag_to_dag
from fate_flow.adapter.bfia.wheels.saver import BfiaScheduleJobSaver
from fate_flow.adapter.bfia.wheels.task import BfiaTaskController
from fate_flow.db import ScheduleJob, ScheduleTask, ScheduleTaskStatus
from fate_flow.entity.code import SchedulingStatusCode
from fate_flow.entity.types import FederatedCommunicationType
from fate_flow.scheduler import SchedulerABC
from fate_flow.utils.log_utils import schedule_logger, exception_to_trace_string


class BfiaScheduler(SchedulerABC):
    def run_do(self):
        logger = schedule_logger(name="bfia_scheduler")
        logger.info("start schedule bfia job")
        jobs = BfiaScheduleJobSaver.query_job(
            status=JobStatus.READY,
            order_by=["priority", "create_time"],
            reverse=[True, False]
        )
        logger.info(f"have {len(jobs)} ready jobs")
        if len(jobs):
            job = jobs[0]
            logger.info(f"schedule ready job {job.f_job_id}")
            try:
                self.schedule_ready_jobs(job)
            except Exception as e:
                schedule_logger(job.f_job_id).exception(e)
            schedule_logger().info("schedule ready jobs finished")

        # running
        schedule_logger().info("start schedule running jobs")
        jobs = BfiaScheduleJobSaver.query_job(status=JobStatus.RUNNING, order_by="create_time", reverse=False)
        schedule_logger().info(f"have {len(jobs)} running jobs")
        for job in jobs:
            schedule_logger().info(f"schedule running job {job.f_job_id}")
            try:
                self.schedule_running_job(job=job)
            except Exception as e:
                schedule_logger(job.f_job_id).exception(e)
                schedule_logger(job.f_job_id).error("schedule job failed")
        schedule_logger().info("schedule running jobs finished")

    @classmethod
    def schedule_ready_jobs(cls, job: ScheduleJob):
        job_id = job.f_job_id
        schedule_logger(job_id).info(f"start job {job_id}")
        response = BfiaFederatedScheduler.start_job(job_id=job_id, node_list=job.f_parties)
        schedule_logger(job_id).info(f"start job {job_id} response: {response}")
        BfiaScheduleJobSaver.update_job_status(job_info={"job_id": job_id, "status": StatusSet.RUNNING})

    def schedule_running_job(self, job: ScheduleJob):
        schedule_logger(job.f_job_id).info("scheduling running job")
        task_scheduling_status_code, tasks = BfiaTaskScheduler.schedule(job=job)
        tasks_status = dict([(task.f_task_name, task.f_status) for task in tasks])
        schedule_logger(job_id=job.f_job_id).info(f"task_scheduling_status_code: {task_scheduling_status_code}, "
                                                  f"tasks_status: {tasks_status.values()}")

        new_job_status = self.calculate_job_status(
            task_scheduling_status_code=task_scheduling_status_code,
            tasks_status=tasks_status.values()
        )

        total, finished_count = self.calculate_job_progress(tasks_status=tasks_status)
        new_progress = float(finished_count) / total * 100
        schedule_logger(job.f_job_id).info(
            f"job status is {new_job_status}, calculate by task status list: {tasks_status}")
        if new_job_status != job.f_status or new_progress != job.f_progress:
            if int(new_progress) - job.f_progress > 0:
                job.f_progress = new_progress
                self.update_job_on_scheduler(schedule_job=job, update_fields=["progress"])
            if new_job_status != job.f_status:
                job.f_status = new_job_status
                self.update_job_on_scheduler(schedule_job=job, update_fields=["status"])
        if EndStatus.contains(job.f_status):
            self.finish(job=job)
        schedule_logger(job.f_job_id).info("finish scheduling running job")

    @classmethod
    def create_all_job(cls, dag, job_id=None):
        dag_schema = DagSchemaSpec(**dag)
        schedule_logger(job_id).info(f"[scheduler]start create all job, dag {dag}")
        submit_result = {
            "job_id": job_id,
            "data": {}
        }
        try:
            job = ScheduleJob()
            job.f_job_id = job_id
            job.f_parties = BfiaJobController.get_job_parties(dag_schema)
            job.f_initiator_party_id = dag_schema.dag.config.initiator.node_id
            job.f_scheduler_party_id = dag_schema.dag.config.initiator.node_id
            job.f_dag = dag_schema.dict()
            job.f_protocol = dag_schema.kind
            job.f_status = StatusSet.READY
            BfiaScheduleJobSaver.create_job(job.to_human_model_dict())
            body = dag_schema.dag.dict(exclude_unset=True)
            body.update({
                "job_id": job_id
            })
            response = BfiaFederatedScheduler.create_job(
                node_list=job.f_parties, command_body=body
            )
            for node_id, resp in response.items():
                if resp.get("code") != ReturnCode.SUCCESS:
                    # stop
                    raise RuntimeError(response)

            job.f_status = StatusSet.READY
            cls.create_schedule_tasks(job, dag_schema)
            schedule_logger(job_id).info(f"[scheduler]submit job successfully, job id is {job.f_job_id}")
            result = {
                "code": ReturnCode.SUCCESS,
            }
            submit_result.update(result)
        except Exception as e:
            schedule_logger(job_id).exception(e)
            submit_result["code"] = ReturnCode.FAILED
            submit_result["msg"] = exception_to_trace_string(e)
        return submit_result

    @classmethod
    def stop_all_job(cls, job_id, task_name=None):
        jobs = BfiaScheduleJobSaver.query_job(job_id=job_id)
        schedule_logger(job_id).info(f"[scheduler]start to stop all job")
        if jobs:
            job = jobs[0]
            body = {
                "job_id": job_id
            }
            if task_name:
                body.update({
                    "task_name": task_name
                })
            resp = BfiaFederatedScheduler.stop_job(
                node_list=job.f_parties, command_body=body
            )
            schedule_logger(job_id).info(f"[scheduler]stop job response: {resp}")

            # update scheduler status
            BfiaScheduleJobSaver.update_job_status(dict(
                job_id=job_id,
                status=JobStatus.FINISHED
            ))

            task_info = {
                "job_id": job_id
            }
            if task_name:
                task_info.update(dict(task_name=task_name))
            else:
                task_info.update(dict(status=TaskStatus.RUNNING))
            tasks = BfiaScheduleJobSaver.query_task(**task_info)

            for task in tasks:
                BfiaScheduleJobSaver.update_task_status(
                    task_info=dict(
                        role=task.f_role,
                        party_id=task.f_party_id,
                        job_id=job_id,
                        task_id=task.f_task_id,
                        task_version=task.f_task_version,
                        status=TaskStatus.FAILED)
                )

                BfiaScheduleJobSaver.update_task_status(
                    task_info=dict(
                        job_id=job_id,
                        task_id=task.f_task_id,
                        task_version=task.f_task_version,
                        status=TaskStatus.FAILED),
                    scheduler_status=True
                )

        else:
            schedule_logger(job_id).exception(f"[scheduler]No found job {job_id}")

    @classmethod
    def query_job_status(cls, job_id):
        jobs = BfiaScheduleJobSaver.query_job(job_id=job_id)
        if jobs:
            job = jobs[0]
            job_status = job.f_status
            all_task_status = {}
            tasks = BfiaScheduleJobSaver.query_task(scheduler_status=True, job_id=job_id)
            for task in tasks:
                all_task_status[task.f_task_name] = task.f_status
            return {
                "job_status": job_status,
                "status": all_task_status
            }
        return {}

    @classmethod
    def audit_confirm(cls, job_id, status):
        return BfiaScheduleJobSaver.update_job_status(job_info={"job_id": job_id, "status": status})

    @classmethod
    def callback_task(cls, task_id, role, status, node_id):
        task = BfiaScheduleJobSaver.query_task(task_id=task_id, party_id=node_id)[0]
        status = BfiaScheduleJobSaver.update_task_status(task_info={
            "job_id": task.f_job_id,
            "role": "",
            "party_id": node_id,
            "task_id": task_id,
            "task_version": 0,
            "status": status
        })
        return status

    @classmethod
    def create_schedule_tasks(cls, job, dag_schema: DagSchemaSpec):
        job_parser = get_dag_parser(dag_schema)
        task_list = [task for task in job_parser.topological_sort()]
        task_parties = {}
        # get task parties
        for name in task_list:
            task_parties[name] = []
            for party in job.f_parties:
                if job_parser.get_runtime_roles_on_party(task_name=name, party_id=party):
                    task_parties[name].append(party)

        # create schedule task
        task_ids = {}
        for name, parties in task_parties.items():
            task_id = BfiaTaskController.generate_task_id()
            task_ids[name] = task_id
            for node_id in parties:
                cls.create_task(
                    job.f_job_id,
                    task_id,
                    node_id,
                    name,
                    job_parser,
                    parties=parties
                )
        cls.create_scheduler_tasks_status(job.f_job_id, task_list, dag_schema, task_ids)

    @classmethod
    def create_task(cls, job_id, task_id, node_id, task_name, job_parser, parties, task_version=0):
        task_node = job_parser.get_task_node(task_name=task_name)
        task_parser = job_parser.task_parser(
            task_node=task_node, job_id=job_id, task_name=task_name, party_id=node_id,
            task_id=task_id, task_version=task_version, parties=parties,
        )
        task = ScheduleTask()
        task.f_job_id = job_id
        task.f_role = ""
        task.f_party_id = node_id
        task.f_task_name = task_name
        task.f_component = task_parser.component_ref
        task.f_task_id = task_id
        task.f_task_version = task_version
        task.f_status = TaskStatus.READY
        task.f_parties = parties
        BfiaScheduleJobSaver.create_task(task.to_human_model_dict())

    @classmethod
    def create_scheduler_tasks_status(cls, job_id, task_list, dag_schema: DagSchemaSpec, task_ids,
                                      task_version=0, auto_retries=0, task_name=None):
        schedule_logger(job_id).info("start create schedule task status info")
        if task_name:
            task_list = [task_name]
        for _task_name in task_list:
            task = ScheduleTaskStatus()
            task.f_job_id = job_id
            task.f_task_name = _task_name
            task.f_task_id = task_ids.get(_task_name)
            task.f_task_version = task_version
            task.f_status = TaskStatus.READY
            task.f_auto_retries = auto_retries
            task.f_sync_type = dag_schema.dag.config.job_params.common.sync_type
            status = BfiaScheduleJobSaver.create_task_scheduler_status(task.to_human_model_dict())
            schedule_logger(job_id).info(f"create schedule task {_task_name} status {status}")

        schedule_logger(job_id).info(f"create schedule task status success： {task_list}")

    @classmethod
    def calculate_job_status(cls, task_scheduling_status_code, tasks_status):
        tmp_status_set = set(tasks_status)
        if len(tmp_status_set) == 1:
            return tmp_status_set.pop()
        else:
            if TaskStatus.RUNNING in tmp_status_set:
                return JobStatus.RUNNING
            if TaskStatus.PENDING in tmp_status_set or TaskStatus.READY in tmp_status_set:
                if task_scheduling_status_code == SchedulingStatusCode.HAVE_NEXT:
                    return JobStatus.RUNNING
            for status in sorted(InterruptStatus.status_list(), key=lambda s: StatusSet.get_level(status=s),
                                 reverse=True):
                if status in tmp_status_set:
                    return status
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
    def update_job_on_scheduler(cls, schedule_job: ScheduleJob, update_fields: list):
        schedule_logger(schedule_job.f_job_id).info(f"try to update job {update_fields} on scheduler")
        jobs = BfiaScheduleJobSaver.query_job(job_id=schedule_job.f_job_id)
        if not jobs:
            raise Exception("Failed to update job status on scheduler")
        job_info = schedule_job.to_human_model_dict(only_primary_with=update_fields)
        for field in update_fields:
            job_info[field] = getattr(schedule_job, "f_%s" % field)
        if "status" in update_fields:
            BfiaScheduleJobSaver.update_job_status(job_info=job_info)
        BfiaScheduleJobSaver.update_job(job_info=job_info)
        schedule_logger(schedule_job.f_job_id).info(f"update job {update_fields} on scheduler finished")

    @classmethod
    def finish(cls, job):
        schedule_logger(job.f_job_id).info(f"job finished, do something...")
        cls.stop_all_job(job_id=job.f_job_id)
        schedule_logger(job.f_job_id).info(f"done")


class BfiaTaskScheduler(object):
    @classmethod
    def schedule(cls, job):
        schedule_logger(job.f_job_id).info("scheduling job tasks")
        dag_schema = DagSchemaSpec(**job.f_dag)
        job_parser = get_dag_parser(dag_schema)
        tasks_group = BfiaScheduleJobSaver.get_status_tasks_asc(job_id=job.f_job_id)
        schedule_logger(job.f_job_id).info(f"tasks group: {tasks_group}")
        waiting_tasks = {}
        job_interrupt = False
        for task in tasks_group.values():
            if task.f_sync_type == FederatedCommunicationType.POLL:
                if task.f_status in [TaskStatus.RUNNING]:
                    cls.collect_task_of_all_party(task=task, parties=job.f_parties)
            else:
                pass
            new_task_status = cls.get_federated_task_status(
                task_name=task.f_task_name,
                job_id=task.f_job_id,
                task_id=task.f_task_id,
                task_version=task.f_task_version
            )
            task_interrupt = False
            task_status_have_update = False
            if new_task_status != task.f_status:
                task_status_have_update = True
                schedule_logger(job.f_job_id).info(f"sync task status {task.f_status} to {new_task_status}")
                task.f_status = new_task_status
                BfiaScheduleJobSaver.update_task_status(task.to_human_model_dict(), scheduler_status=True)
            if InterruptStatus.contains(new_task_status):
                task_interrupt = True
                job_interrupt = True
            if task.f_status == TaskStatus.READY:
                waiting_tasks[task.f_task_name] = task
            elif task_status_have_update and EndStatus.contains(task.f_status) or task_interrupt:
                schedule_logger(task.f_job_id).info(f"stop task with status: {task.f_status}")
                BfiaFederatedScheduler.stop_job(
                    node_list=job.f_parties,
                    command_body={
                        "job_id": task.f_job_id,
                        "task_name": task.f_task_name
                })
        scheduling_status_code = SchedulingStatusCode.NO_NEXT
        schedule_logger(job.f_job_id).info(f"job interrupt status {job_interrupt}")
        schedule_logger(job.f_job_id).info(f"waiting tasks: {waiting_tasks}")
        if not job_interrupt:
            for task_id, waiting_task in waiting_tasks.items():

                dependent_tasks = job_parser.infer_dependent_tasks(
                    translate_bfia_dag_to_dag(dag_schema).dag.tasks[waiting_task.f_task_name].inputs
                )
                schedule_logger(job.f_job_id).info(f"task {waiting_task.f_task_name} dependent tasks:{dependent_tasks}")
                for task_name in dependent_tasks:
                    dependent_task = tasks_group[task_name]
                    if dependent_task.f_status != TaskStatus.SUCCESS:
                        break
                else:
                    scheduling_status_code = SchedulingStatusCode.HAVE_NEXT
                    status_code = cls.start_task(
                        job_id=waiting_task.f_job_id,
                        task_name=waiting_task.f_task_name,
                        task_id=waiting_task.f_task_id,
                        task_version=waiting_task.f_task_version
                    )
                    if status_code == SchedulingStatusCode.FAILED:
                        schedule_logger(job.f_job_id).info(f"task status code: {status_code}")
                        scheduling_status_code = SchedulingStatusCode.FAILED
                        waiting_task.f_status = StatusSet.FAILED
                        BfiaFederatedScheduler.stop_job(
                            node_list=job.f_parties,
                            command_body={
                                "job_id": job.f_job_id,
                                "task_name": waiting_task.f_task_name
                            })
        else:
            schedule_logger(job.f_job_id).info("have cancel signal, pass start job tasks")
        schedule_logger(job.f_job_id).info("finish scheduling job tasks")
        return scheduling_status_code, tasks_group.values()

    @classmethod
    def start_task(cls, job_id, task_name, task_id, task_version):
        schedule_logger(job_id).info("try to start task {} {}".format(task_id, task_name))

        tasks = BfiaScheduleJobSaver.query_task(task_id=task_id, task_name=task_name)
        response_list = BfiaFederatedScheduler.start_task(
            task_id=task_id, task_name=task_name, job_id=job_id, node_list=tasks[0].f_parties
        )
        schedule_logger(job_id).info(f"start task response: {response_list}")
        for resp in response_list.values():
            if resp["code"] != ReturnCode.SUCCESS:
                return SchedulingStatusCode.FAILED
        else:
            # update scheduler task info to running
            task_info = dict(
                job_id=job_id,
                task_name=task_name,
                task_id=task_id,
                status=TaskStatus.RUNNING,
                task_version=task_version
            )
            BfiaScheduleJobSaver.update_task_status(
                task_info=task_info,
                scheduler_status=True
            )
            for task in tasks:
                task_info.update({
                    "role": task.f_role,
                    "party_id": task.f_party_id
                })
                BfiaScheduleJobSaver.update_task_status(
                    task_info=task_info

                )
            return SchedulingStatusCode.SUCCESS

    @classmethod
    def collect_task_of_all_party(cls, task, parties):
        federated_response = BfiaFederatedScheduler.poll_task_all(
            node_list=parties,
            task_id=task.f_task_id
        )
        for _party_id, party_response in federated_response.items():
            if party_response["code"] == ReturnCode.SUCCESS:
                schedule_logger(task.f_job_id).info(
                    f"collect party id {_party_id} task {task.f_task_name} info: {party_response['data']}")
                task_info = {
                    "job_id": task.f_job_id,
                    "task_id": task.f_task_id,
                    "task_version": task.f_task_version,
                    "role": "",
                    "party_id": _party_id,
                    "status": party_response["data"].get("status")
                }
                BfiaScheduleJobSaver.update_task_status(task_info=task_info)

    @classmethod
    def get_federated_task_status(cls, task_name, job_id, task_id, task_version):
        tasks_on_all_party = BfiaScheduleJobSaver.query_task(task_id=task_id, task_version=task_version)
        tasks_party_status = [task.f_status for task in tasks_on_all_party]
        status = BfiaTaskController.calculate_multi_party_task_status(tasks_party_status)
        schedule_logger(job_id=job_id).info(
            "task {} {} {} status is {}, calculate by task party status list: {}".format(
                task_name,
                task_id,
                task_version,
                status,
                tasks_party_status
            ))
        return status
