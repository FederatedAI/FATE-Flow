import json
import os.path
from copy import deepcopy

from fate_flow.adapter.bfia.settings import VOLUME
from fate_flow.adapter.bfia.utils.entity.status import TaskStatus
from fate_flow.adapter.bfia.utils.spec.job import DagSchemaSpec
from fate_flow.adapter.bfia.wheels.federated import BfiaFederatedScheduler
from fate_flow.adapter.bfia.wheels.parser import get_dag_parser
from fate_flow.adapter.bfia.wheels.saver import BfiaJobSaver as JobSaver
from fate_flow.controller.task import TaskController
from fate_flow.db import Task
from fate_flow.engine.devices.container import ContainerdEngine
from fate_flow.entity.types import PROTOCOL, LauncherType
from fate_flow.manager.service.provider_manager import ProviderManager
from fate_flow.runtime.system_settings import PARTY_ID
from fate_flow.utils import job_utils
from fate_flow.utils.log_utils import schedule_logger


class BfiaTaskController(TaskController):
    @classmethod
    def create_local_tasks(cls, job_id, task_id, task_name, dag):
        schedule_logger(job_id).info(f"start create tasks")
        dag_schema = DagSchemaSpec.parse_obj(dag)
        job_parser = get_dag_parser(dag_schema)
        # get runtime roles
        roles = job_parser.get_runtime_roles_on_party(task_name, party_id=PARTY_ID)
        tasks = []
        for role in roles:
            tasks.append(cls.create_local_task(job_id, role, PARTY_ID, task_id, task_name, dag_schema, job_parser))
        schedule_logger(job_id).info("create tasks success")
        return tasks

    @classmethod
    def create_local_task(
            cls, job_id, role, node_id, task_id, task_name, dag_schema, job_parser, task_version=0
    ):
        execution_id = job_utils.generate_session_id(task_id, task_version, role, node_id)
        task_node = job_parser.get_task_node(task_name=task_name)
        task_parser = job_parser.task_parser(
            task_node=task_node, job_id=job_id, task_name=task_name, role=role, party_id=node_id,
            task_id=task_id, task_version=task_version
        )
        task_parameters = task_parser.task_parameters
        schedule_logger(job_id).info(f"task {task_name} role {role} part id {node_id} task_parameters"
                                     f" {task_parameters.dict()}, provider: {task_parser.provider}")
        task = Task()
        task.f_job_id = job_id
        task.f_role = role
        task.f_party_id = node_id
        task.f_task_name = task_name
        task.f_component = task_parser.component_ref
        task.f_task_id = task_id
        task.f_task_version = task_version
        task.f_scheduler_party_id = dag_schema.dag.config.initiator.node_id
        task.f_status = TaskStatus.READY
        task.f_party_status = TaskStatus.READY
        task.f_execution_id = execution_id
        task.f_provider_name = task_parser.provider
        task.f_sync_type = dag_schema.dag.config.job_params.common.sync_type
        task.f_task_run = {}
        task.f_task_cores = 0
        task.f_protocol = PROTOCOL.BFIA
        task.f_component_parameters = task_parameters.dict()
        JobSaver.create_task(task.to_human_model_dict())
        return task

    @classmethod
    def start_tasks(cls, job_id, task_id, task_name):
        # creating a task before starting
        jobs = JobSaver.query_job(job_id=job_id)
        if not jobs:
            raise RuntimeError(f"No found job {job_id}")
        job = jobs[0]
        tasks = cls.create_local_tasks(job_id, task_id, task_name, job.f_dag)
        status_list = []

        # start
        for task in tasks:
            schedule_logger(job_id).info(f"start {task.f_role} {task.f_party_id} task")
            status_list.append(cls.start_task(task))
        if TaskStatus.FAILED in status_list:
            return False
        return True

    @classmethod
    def stop_local_task(cls, job_id, task_name):
        stop_status = TaskStatus.FAILED
        tasks = JobSaver.query_task(job_id=job_id, task_name=task_name)
        for task in tasks:

            schedule_logger(job_id=job_id).info(f"[stop]start to kill task {task.f_task_name} "
                                                f"status {task.f_task_status}")
            status = cls.stop_task(task, stop_status=stop_status)
            schedule_logger(job_id=job_id).info(f"[stop]Kill {task.f_task_name} task completed: {status}")

    @classmethod
    def callback_task(cls, task_id, status, role):
        BfiaTaskController.update_task_info(
            task_info={
                "task_id": task_id,
                "party_status": status,
                "role": role
            },
            callback=BfiaTaskController.update_task_status
        )

    @classmethod
    def update_task_info(cls, task_info, callback):
        info = deepcopy(task_info)
        if "task_version" not in info:
            task_info = JobSaver.query_task(task_id=info.get("task_id"))
            for task in task_info:
                if "role" not in info:
                    info["role"] = task.f_role
                info["party_id"] = task.f_party_id
                info["task_version"] = task.f_task_version
                info["job_id"] = task.f_job_id
                callback(info)
        else:
            callback(info)

    @classmethod
    def update_task(cls, task_info):
        update_status = False
        try:
            update_status = JobSaver.update_task(task_info=task_info)
        except Exception as e:
            schedule_logger(task_info["job_id"]).exception(e)
        finally:
            return update_status

    @classmethod
    def update_task_status(cls, task_info, scheduler_party_id=None, sync_type=None):
        schedule_logger(task_info["job_id"]).info(f"update task status to {task_info.get('party_status')}")
        status = task_info.get("status") or task_info.get("party_status")
        if status:
            task_info["status"] = status.upper()
            task_info["party_status"] = status.upper()
        update_status = JobSaver.update_task_status(task_info=task_info)
        return update_status

    @classmethod
    def poll_task(cls, task_id, role):
        tasks = JobSaver.query_task(task_id=task_id, party_id=PARTY_ID)
        if not tasks:
            raise RuntimeError(f"No found task: {task_id} node id {PARTY_ID}")
        status = cls.calculate_multi_party_task_status([task.f_party_status for task in tasks])
        return status

    @classmethod
    def callback_task_to_scheduler(cls, scheduler_party_id, task_id, status, role):
        task_info = {
            "task_id": task_id,
            "status": status,
            "role": role
        }
        return BfiaFederatedScheduler.request_report_task(party_id=scheduler_party_id, command_body=task_info)

    @classmethod
    def query_tasks_status(cls, job_id):
        all_status = {}
        status = {}
        for task in JobSaver.query_task(job_id=job_id):
            if task.f_task_id not in all_status:
                all_status[task.f_task_id] = [task.f_party_status]
            else:
                all_status[task.f_task_id].append(task.f_party_status)

        for task_id, status_list in all_status.items():
            status[task_id] = cls.calculate_multi_party_task_status(status_list)
        return status

    @classmethod
    def calculate_multi_party_task_status(cls, tasks_party_status):
        tmp_status_set = set(tasks_party_status)
        if len(tmp_status_set) == 1:
            return tmp_status_set.pop()
        else:
            if TaskStatus.FAILED in tmp_status_set:
                return TaskStatus.FAILED
            if TaskStatus.RUNNING in tmp_status_set:
                return TaskStatus.RUNNING
            if TaskStatus.READY in tmp_status_set:
                return TaskStatus.READY
            if TaskStatus.PENDING in tmp_status_set:
                return TaskStatus.PENDING
            if TaskStatus.SUCCESS in tmp_status_set:
                return TaskStatus.SUCCESS

    @classmethod
    def build_task_engine(cls, provider_name, launcher_name=LauncherType.DEFAULT):
        provider = ProviderManager.get_provider_by_provider_name(provider_name)
        return BfiaContainerd(provider)

    @staticmethod
    def generate_task_id():
        import uuid
        return str(uuid.uuid4())


class BfiaContainerd(ContainerdEngine):
    @classmethod
    def _get_environment(cls, task: Task, run_parameters):
        return cls._flatten_dict(run_parameters)

    @classmethod
    def _get_volume(cls, task):
        # return {
        #     os.path.join(LOCAL_LOG_PATH, task.f_job_id, task.f_role, task.f_task_name):
        #         {
        #             'bind': CONTAINER_LOG_PATH,
        #             'mode': 'rw'
        #         }
        # }

        return VOLUME

    @classmethod
    def _flatten_dict(cls, data, parent_key='', sep='.', loop=True):
        special_fields = ["input", "output", "parameter"]
        items = {}
        for key, value in data.items():
            new_key = f"{parent_key}{sep}{key}" if parent_key else key
            # Determine the location of special fields
            for field in special_fields:
                if new_key.endswith(f"{sep}{field}"):
                    # continue
                    items.update(cls._flatten_dict(value, new_key, sep=sep, loop=False))
                    break
            else:
                if isinstance(value, dict) and loop:
                    items.update(cls._flatten_dict(value, new_key, sep=sep))
                else:
                    if not loop:
                        if isinstance(value, dict) or isinstance(value, list):
                            value = json.dumps(value)
                    items[new_key] = value
        return items

    def exit_with_exception(self, task: Task):
        return self.manager.exit_with_exception(self._get_name(task))
