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
import os
import shutil
import functools
import importlib
from copy import deepcopy

from fate_flow.controller.task import TaskController
from fate_flow.db import Job
from fate_flow.engine.storage import Session
from fate_flow.entity.spec.dag import DAGSchema, InheritConfSpec, JobConfSpec
from fate_flow.entity.types import EndStatus, JobStatus, TaskStatus, EngineType, ComputingEngine
from fate_flow.entity.code import ReturnCode
from fate_flow.errors.server_error import NoFoundJob, JobParamsError
from fate_flow.manager.outputs.metric import OutputMetric
from fate_flow.manager.outputs.model import PipelinedModel, ModelMeta
from fate_flow.manager.outputs.data import OutputDataTracking
from fate_flow.manager.service.resource_manager import ResourceManager
from fate_flow.manager.operation.job_saver import JobSaver
from fate_flow.controller.federated import FederatedScheduler
from fate_flow.runtime.job_default_config import JobDefaultConfig
from fate_flow.runtime.system_settings import ENGINES, IGNORE_RESOURCE_ROLES, COMPUTING_CONF, PARTY_ID, LOCAL_PARTY_ID
from fate_flow.utils import job_utils
from fate_flow.utils.base_utils import current_timestamp
from fate_flow.utils.job_utils import get_job_log_directory, save_job_dag
from fate_flow.utils.log_utils import schedule_logger


class Adapter(object):
    @staticmethod
    def fun(func):
        @functools.wraps(func)
        def _wrapper(*args, **kwargs):
            dag_schema = args[0]
            schema = DAGSchema(**dag_schema)
            module_name = schema.kind
            package = f'fate_flow.adapter.{module_name}.utils.job'
            if hasattr(importlib.import_module(package), func.__name__):
                return getattr(importlib.import_module(package), func.__name__)
            else:
                return func(*args, **kwargs)
        return _wrapper


class JobController(object):
    @classmethod
    @Adapter.fun
    def request_create_job(cls, dag_schema: dict, user_name: str = None, is_local=False):
        schema = DAGSchema(**dag_schema)
        cls.update_job_default_params(schema, is_local=is_local)
        cls.check_job_params(schema)
        response = FederatedScheduler.request_create_job(
            party_id=schema.dag.conf.scheduler_party_id,
            initiator_party_id=schema.dag.conf.initiator_party_id,
            command_body=schema.dict()
        )
        if user_name and response.get("code") == ReturnCode.Base.SUCCESS:
            JobSaver.update_job_user(job_id=response.get("job_id"), user_name=user_name)
        if response and isinstance(response, dict) and response.get("code") == ReturnCode.Base.SUCCESS:
            save_job_dag(job_id=response.get("job_id"), dag=dag_schema)
        return response

    @classmethod
    @Adapter.fun
    def request_stop_job(cls, job_id):
        schedule_logger(job_id).info(f"stop job on this party")
        jobs = JobSaver.query_job(job_id=job_id)
        if not jobs:
            raise NoFoundJob(job_id=job_id)
        status = JobStatus.CANCELED
        kill_status, kill_details = JobController.stop_jobs(job_id=job_id, stop_status=status)
        schedule_logger(job_id).info(f"stop job on this party status {kill_status}")
        schedule_logger(job_id).info(f"request stop job to {status}")
        response = FederatedScheduler.request_stop_job(
            party_id=jobs[0].f_scheduler_party_id,
            job_id=job_id, stop_status=status
        )
        schedule_logger(job_id).info(f"stop job response: {response}")
        return response

    @classmethod
    def request_rerun_job(cls, job):
        schedule_logger(job.f_job_id).info(f"request rerun job {job.f_job_id}")
        response = FederatedScheduler.request_rerun_job(party_id=job.f_scheduler_party_id, job_id=job.f_job_id)
        schedule_logger(job.f_job_id).info(f"rerun job response: {response}")
        return response

    @classmethod
    def create_job(cls, dag, schema_version, job_id: str, role: str, party_id: str):
        # create job and task
        schedule_logger(job_id).info(f"start create job {job_id} {role} {party_id}")
        dag_schema = DAGSchema(dag=dag, schema_version=schema_version)
        job_info = {
            "job_id": job_id,
            "role": role,
            "party_id": party_id,
            "dag": dag_schema.dict(),
            "progress": 0,
            "parties": [party.dict() for party in dag_schema.dag.parties],
            "initiator_party_id": dag_schema.dag.conf.initiator_party_id,
            "scheduler_party_id": dag_schema.dag.conf.scheduler_party_id,
            "status": JobStatus.READY,
            "model_id": dag_schema.dag.conf.model_id,
            "model_version": dag_schema.dag.conf.model_version
        }
        party_parameters, task_run, task_cores = cls.adapt_party_parameters(dag_schema, role)
        schedule_logger(job_id).info(f"party_job_parameters: {party_parameters}")
        schedule_logger(job_id).info(f"role {role} party_id {party_id} task run: {task_run}, task cores {task_cores}")
        job_info.update(party_parameters)
        JobSaver.create_job(job_info=job_info)
        # create task
        TaskController.create_tasks(job_id, role, party_id, dag_schema, task_run=task_run, task_cores=task_cores)

    @classmethod
    def start_job(cls, job_id, role, party_id, extra_info=None):
        schedule_logger(job_id).info(f"try to start job on {role} {party_id}")
        job_info = {
            "job_id": job_id,
            "role": role,
            "party_id": party_id,
            "status": JobStatus.RUNNING,
            "start_time": current_timestamp()
        }
        if extra_info:
            schedule_logger(job_id).info(f"extra info: {extra_info}")
            job_info.update(extra_info)
        try:
            cls.inheritance_job(job_id, role, party_id)
        except Exception as e:
            schedule_logger(job_id).exception(e)
            job_info.update({"status": JobStatus.FAILED})
        finally:
            cls.update_job_status(job_info=job_info)
            cls.update_job(job_info=job_info)
            schedule_logger(job_id).info(f"start job on {role} {party_id} {job_info.get('status')}")

    @classmethod
    def inheritance_job(cls, job_id, role, party_id):
        job = JobSaver.query_job(job_id=job_id, role=role, party_id=party_id)[0]
        if job.f_inheritance:
            schedule_logger(job_id).info(f"start inherit job {job_id}, inheritance: {job.f_inheritance}")
            JobInheritance.load(job)

    @classmethod
    def update_job_status(cls, job_info):
        update_status = JobSaver.update_job_status(job_info=job_info)
        if update_status and EndStatus.contains(job_info.get("status")):
            ResourceManager.return_job_resource(
                job_id=job_info["job_id"], role=job_info["role"], party_id=job_info["party_id"])
        return update_status

    @classmethod
    def stop_jobs(cls, job_id, role=None, party_id=None, stop_status=JobStatus.FAILED):
        if not stop_status:
            stop_status = JobStatus.FAILED
        if role and party_id:
            jobs = JobSaver.query_job(
                job_id=job_id, role=role, party_id=party_id)
        else:
            jobs = JobSaver.query_job(job_id=job_id)
        kill_status = True
        kill_details = {}
        for job in jobs:
            kill_job_status, kill_job_details = cls.stop_job(
                job=job, stop_status=stop_status)
            kill_status = kill_status & kill_job_status
            kill_details[job_id] = kill_job_details
        return kill_status, kill_details

    @classmethod
    def stop_job(cls, job, stop_status):
        tasks = JobSaver.query_task(
            job_id=job.f_job_id, role=job.f_role, party_id=job.f_party_id, only_latest=True, reverse=True)
        kill_status = True
        kill_details = {}
        for task in tasks:
            if task.f_status in [TaskStatus.SUCCESS, TaskStatus.WAITING, TaskStatus.PASS]:
                continue
            kill_task_status = TaskController.stop_task(task, stop_status)
            kill_status = kill_status & kill_task_status
            kill_details[task.f_task_id] = 'success' if kill_task_status else 'failed'
        if kill_status:
            job_info = job.to_human_model_dict(only_primary_with=["status"])
            job_info["status"] = stop_status
            JobController.update_job_status(job_info)
        return kill_status, kill_details

    @classmethod
    def update_job(cls, job_info):
        return JobSaver.update_job(job_info=job_info)

    @classmethod
    def query_job(cls, **kwargs):
        query_filters = {}
        for k, v in kwargs.items():
            if v is not None:
                query_filters[k] = v
        return JobSaver.query_job(**query_filters)

    @classmethod
    def query_job_list(cls, limit, page, job_id, description, partner, party_id, role, status, order_by, order,
                       user_name):
        # Provided to the job display page
        offset = limit * (page - 1)
        query = {'tag': ('!=', 'submit_failed')}
        if job_id:
            query["job_id"] = ('contains', job_id)
        if description:
            query["description"] = ('contains', description)
        if party_id:
            query["party_id"] = ('contains', party_id)
        if partner:
            query["partner"] = ('contains', partner)
        if role:
            query["role"] = ('in_', set(role))
        if status:
            query["status"] = ('in_', set(status))
        by = []
        if order_by:
            by.append(order_by)
        if order:
            by.append(order)
        if not by:
            by = ['create_time', 'desc']
        if user_name:
            query["user_name"] = ("==", user_name)
        jobs, count = JobSaver.list_job(limit, offset, query, by)
        jobs = [job.to_human_model_dict() for job in jobs]
        for job in jobs:
            job['partners'] = set()
            for _r in job['parties']:
                job['partners'].update(_r.get("party_id"))
            job['partners'].discard(job['party_id'])
            job['partners'] = sorted(job['partners'])
        return count, jobs

    @classmethod
    def query_task_list(cls, limit, page, job_id, role, party_id, task_name, order_by, order):
        offset = limit * (page - 1)

        query = {}
        if job_id:
            query["job_id"] = job_id
        if role:
            query["role"] = role
        if party_id:
            query["party_id"] = party_id
        if task_name:
            query["task_name"] = task_name
        by = []
        if by:
            by.append(order_by)
        if order:
            by.append(order)
        if not by:
            by = ['create_time', 'desc']

        tasks, count = JobSaver.list_task(limit, offset, query, by)
        return count, [task.to_human_model_dict() for task in tasks]

    @classmethod
    def query_tasks(cls, **kwargs):
        query_filters = {}
        for k, v in kwargs.items():
            if v is not None:
                query_filters[k] = v
        return JobSaver.query_task(**query_filters)

    @classmethod
    def clean_queue(cls):
        # stop waiting job
        jobs = JobSaver.query_job(status=JobStatus.WAITING)
        clean_status = {}
        for job in jobs:
            status = FederatedScheduler.request_stop_job(party_id=job.f_scheduler_party_id,job_id=job.f_job_id, stop_status=JobStatus.CANCELED)
            clean_status[job.f_job_id] = status
        return clean_status

    @classmethod
    def clean_job(cls, job_id):
        jobs = JobSaver.query_job(job_id=job_id)
        tasks = JobSaver.query_task(job_id=job_id)
        if not jobs:
            raise NoFoundJob(job_id=job_id)
        FederatedScheduler.request_stop_job(
            party_id=jobs[0].f_scheduler_party_id,job_id=jobs[0].f_job_id, stop_status=JobStatus.CANCELED
        )
        for task in tasks:
            # metric
            try:
                OutputMetric(job_id=task.f_job_id, role=task.f_role, party_id=task.f_party_id,
                             task_name=task.f_task_name,
                             task_id=task.f_task_id, task_version=task.f_task_version).delete_metrics()
                schedule_logger(task.f_job_id).info(f'delete {task.f_job_id} {task.f_role} {task.f_party_id}'
                                                    f' {task.f_task_name} metric data success')
            except Exception as e:
                pass

            # data
            try:
                datas = OutputDataTracking.query(
                    job_id=task.f_job_id,
                    role=task.f_role,
                    party_id=task.f_party_id,
                    task_name=task.f_task_name,
                    task_id=task.f_task_id,
                    task_version=task.f_task_version
                )
                with Session() as sess:
                    for data in datas:
                        table = sess.get_table(name=data.f_name, namespace=data.f_namespace)
                        if table:
                            table.destroy()
            except Exception as e:
                pass

            # model
            try:
                PipelinedModel.delete_model(job_id=task.f_job_id, role=task.f_role,
                                            party_id=task.f_party_id, task_name=task.f_task_name)
                schedule_logger(task.f_job_id).info(f'delete {task.f_job_id} {task.f_role} {task.f_party_id}'
                                                    f' {task.f_task_name} model success')
            except Exception as e:
                pass
        # JobSaver.delete_job(job_id=job_id)

    @staticmethod
    def add_notes(job_id, role, party_id, notes):
        job_info = {
            "job_id": job_id,
            "role": role,
            "party_id": party_id,
            "description": notes
        }
        return JobSaver.update_job(job_info)

    @classmethod
    def adapt_party_parameters(cls, dag_schema: DAGSchema, role):
        cores, task_run, task_cores = cls.calculate_resource(dag_schema, role)
        job_info = {"cores": cores, "remaining_cores": cores}
        if dag_schema.dag.conf.inheritance:
            job_info.update({"inheritance": dag_schema.dag.conf.inheritance.dict()})
        return job_info, task_run, task_cores

    @classmethod
    def calculate_resource(cls, dag_schema: DAGSchema, role):
        cores = dag_schema.dag.conf.cores if dag_schema.dag.conf.cores else JobDefaultConfig.job_cores
        if dag_schema.dag.conf.task and dag_schema.dag.conf.task.run:
            task_run = dag_schema.dag.conf.task.run
        else:
            task_run = {}
        task_cores = cores
        default_task_run = deepcopy(JobDefaultConfig.task_run.get(ENGINES.get(EngineType.COMPUTING), {}))
        if ENGINES.get(EngineType.COMPUTING) == ComputingEngine.SPARK:
            if "num-executors" not in task_run:
                task_run["num-executors"] = default_task_run.get("num-executors")
            if "executor-cores" not in task_run:
                task_run["executor-cores"] = default_task_run.get("executor-cores")
            if role in IGNORE_RESOURCE_ROLES:
                task_run["num-executors"] = 1
                task_run["executor-cores"] = 1
            task_cores = int(task_run.get("num-executors")) * (task_run.get("executor-cores"))
            if task_cores > cores:
                cores = task_cores
        if ENGINES.get(EngineType.COMPUTING) == ComputingEngine.EGGROLL:
            if "eggroll.session.processors.per.node" not in task_run:
                task_run["eggroll.session.processors.per.node"] = \
                    default_task_run.get("eggroll.session.processors.per.node")
            task_cores = int(task_run.get("eggroll.session.processors.per.node")) * COMPUTING_CONF.get(
                ComputingEngine.EGGROLL).get("nodes")
            if task_cores > cores:
                cores = task_cores
            if role in IGNORE_RESOURCE_ROLES:
                task_run["eggroll.session.processors.per.node"] = 1
        if ENGINES.get(EngineType.COMPUTING) == ComputingEngine.STANDALONE:
            if "cores" not in task_run:
                task_run["cores"] = default_task_run.get("cores")
            task_cores = int(task_run.get("cores"))
            if task_cores > cores:
                cores = task_cores
            if role in IGNORE_RESOURCE_ROLES:
                task_run["cores"] = 1
        if role in IGNORE_RESOURCE_ROLES:
            cores = 0
            task_cores = 0
        return cores, task_run, task_cores

    @classmethod
    def check_job_params(cls, dag_schema: DAGSchema):
        # check inheritance
        job_utils.inheritance_check(dag_schema.dag.conf.inheritance)

        # check model warehouse
        model_warehouse = dag_schema.dag.conf.model_warehouse
        if model_warehouse:
            if not ModelMeta.query(model_id=model_warehouse.model_id, model_version=model_warehouse.model_version):
                raise JobParamsError(
                    model_id=model_warehouse.model_id,
                    model_version=model_warehouse.model_version,
                    position="dag_schema.dag.conf.model_warehouse"
                )

    @classmethod
    def update_job_default_params(cls, dag_schema: DAGSchema, is_local: bool = False):
        if not dag_schema.dag.conf:
            dag_schema.dag.conf = JobConfSpec()
        dag_schema.dag.conf.initiator_party_id = PARTY_ID
        if not dag_schema.dag.conf.scheduler_party_id:
            if not is_local:
                dag_schema.dag.conf.scheduler_party_id = PARTY_ID
            else:
                dag_schema.dag.conf.scheduler_party_id = LOCAL_PARTY_ID
        if not dag_schema.dag.conf.computing_partitions:
            dag_schema.dag.conf.computing_partitions = JobDefaultConfig.computing_partitions
        return dag_schema


class JobInheritance:
    @classmethod
    def load(cls, job: Job):
        # load inheritance: data、model、metric、logs
        inheritance = InheritConfSpec(**job.f_inheritance)
        source_task_list = JobSaver.query_task(job_id=inheritance.job_id, role=job.f_role, party_id=job.f_party_id)
        task_list = JobSaver.query_task(job_id=job.f_job_id, role=job.f_role, party_id=job.f_party_id)
        target_task_list = [task for task in task_list if task.f_task_name in inheritance.task_list]
        cls.load_logs(job, inheritance)
        cls.load_output_tracking(job.f_job_id, source_task_list, target_task_list)
        cls.load_model_meta(job.f_job_id, source_task_list, target_task_list, job.f_model_id, job.f_model_version)
        cls.load_metric(job.f_job_id, source_task_list, target_task_list)
        cls.load_status(job.f_job_id, source_task_list, target_task_list)

    @classmethod
    def load_logs(cls, job: Job, inheritance: InheritConfSpec):
        schedule_logger(job.f_job_id).info("start load job logs")
        for task_name in inheritance.task_list:
            source_path = os.path.join(get_job_log_directory(inheritance.job_id), job.f_role, job.f_party_id, task_name)
            target_path = os.path.join(get_job_log_directory(job.f_job_id), job.f_role, job.f_party_id, task_name)
            if os.path.exists(source_path):
                if os.path.exists(target_path):
                    shutil.rmtree(target_path)
                shutil.copytree(source_path, target_path)
        schedule_logger(job.f_job_id).info("load job logs success")

    @classmethod
    def load_output_tracking(cls, job_id, source_task_list, target_task_list):
        def callback(target_task, source_task):
            output_tracking = OutputDataTracking.query(
                job_id=source_task.f_job_id,
                role=source_task.f_role,
                party_id=source_task.f_party_id,
                task_name=source_task.f_task_name,
                task_id=source_task.f_task_id,
                task_version=source_task.f_task_version
            )
            for t in output_tracking:
                _t = t.to_human_model_dict()
                _t.update({
                    "job_id": target_task.f_job_id,
                    "task_id": target_task.f_task_id,
                    "task_version": target_task.f_task_version,
                    "role": target_task.f_role,
                    "party_id": target_task.f_party_id
                })
                OutputDataTracking.create(_t)
        schedule_logger(job_id).info("start load output tracking")
        cls.load_do(source_task_list, target_task_list, callback)
        schedule_logger(job_id).info("load output tracking success")

    @classmethod
    def load_model_meta(cls, job_id, source_task_list, target_task_list, model_id, model_version):
        def callback(target_task, source_task):
            _model_metas = ModelMeta.query(
                job_id=source_task.f_job_id,
                role=source_task.f_role,
                party_id=source_task.f_party_id,
                task_name=source_task.f_task_name
            )
            for _meta in _model_metas:
                _md = _meta.to_human_model_dict()
                _md.update({
                    "job_id": target_task.f_job_id,
                    "task_id": target_task.f_task_id,
                    "task_version": target_task.f_task_version,
                    "role": target_task.f_role,
                    "party_id": target_task.f_party_id,
                    "model_id": model_id,
                    "model_version": model_version
                })
                ModelMeta.save(**_md)
        schedule_logger(job_id).info("start load model meta")
        cls.load_do(source_task_list, target_task_list, callback)
        schedule_logger(job_id).info("load model meta success")

    @classmethod
    def load_metric(cls, job_id, source_task_list, target_task_list):
        def callback(target_task, source_task):
            OutputMetric(
                job_id=source_task.f_job_id,
                role=source_task.f_role,
                party_id=source_task.f_party_id,
                task_name=source_task.f_task_name,
                task_id=source_task.f_task_id,
                task_version=source_task.f_task_version
            ).save_as(
                job_id=target_task.f_job_id,
                role=target_task.f_role,
                party_id=target_task.f_party_id,
                task_name=target_task.f_task_name,
                task_id=target_task.f_task_id,
                task_version=target_task.f_task_version
            )
        schedule_logger(job_id).info("start load metric")
        cls.load_do(source_task_list, target_task_list, callback)
        schedule_logger(job_id).info("load metric success")

    @classmethod
    def load_status(cls, job_id, source_task_list, target_task_list):
        def callback(target_task, source_task):
            task_info = {
                "job_id": target_task.f_job_id,
                "task_id": target_task.f_task_id,
                "task_version": target_task.f_task_version,
                "role": target_task.f_role,
                "party_id": target_task.f_party_id
            }
            update_info = {}
            update_list = ["cmd", "elapsed", "end_time", "engine_conf", "party_status", "run_ip",
                           "run_pid", "start_time", "status", "worker_id"]
            for k in update_list:
                update_info[k] = getattr(source_task, f"f_{k}")
            task_info.update(update_info)
            schedule_logger(task_info["job_id"]).info(
                "try to update task {} {}".format(task_info["task_id"], task_info["task_version"]))
            schedule_logger(task_info["job_id"]).info("update info: {}".format(update_info))
            JobSaver.update_task(task_info)
            TaskController.update_task_status(task_info)
        schedule_logger(job_id).info("start load status")
        cls.load_do(source_task_list, target_task_list, callback)
        schedule_logger(job_id).info("load status success")

    @staticmethod
    def load_do(source_task_list, target_task_list, callback):
        for source_task in source_task_list:
            for target_task in target_task_list:
                if target_task.f_task_name == source_task.f_task_name:
                    callback(target_task, source_task)
