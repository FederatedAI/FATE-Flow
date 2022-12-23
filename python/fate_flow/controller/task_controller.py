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
from copy import deepcopy

from fate_flow.db.db_models import Task
from fate_flow.engine.computing import build_engine
from fate_flow.hub.parser.default import DAGSchema
from fate_flow.hub.flow_hub import FlowHub
from fate_flow.manager.worker_manager import WorkerManager
from fate_flow.scheduler.federated_scheduler import FederatedScheduler
from fate_flow.entity.run_status import EndStatus, TaskStatus
from fate_flow.operation.job_saver import JobSaver
from fate_flow.utils import job_utils
from fate_flow.utils.base_utils import current_timestamp, json_dumps
from fate_flow.utils.log_utils import schedule_logger


class TaskController(object):
    INITIATOR_COLLECT_FIELDS = ["status", "party_status", "start_time", "update_time", "end_time", "elapsed"]

    @classmethod
    def create_task(cls, role, party_id, run_on_this_party, task_info):
        pass

    @classmethod
    def start_task(cls, job_id, role, party_id, task_id, task_version):
        schedule_logger(job_id).info(
            f"try to start task {task_id} {task_version} on {role} {party_id} executor subprocess")
        task_executor_process_start_status = False
        task_info = {
            "job_id": job_id,
            "task_id": task_id,
            "task_version": task_version,
            "role": role,
            "party_id": party_id,
        }
        is_failed = False
        try:
            task = JobSaver.query_task(task_id=task_id, task_version=task_version, role=role, party_id=party_id)[0]
            run_parameters = task.f_component_parameters
            # update runtime parameters
            job = JobSaver.query_job(job_id=job_id, role=role, party_id=party_id)[0]
            dag_schema = DAGSchema(**job.f_dag)
            job_parser = FlowHub.load_job_parser(dag_schema)
            task_node = job_parser.get_task_node(task_name=task.f_task_name)
            task_parser = FlowHub.load_task_parser(
                task_node=task_node, job_id=job_id, task_name=task.f_task_name, role=role,
                party_id=party_id, parties=dag_schema.dag.parties
            )
            task_parser.update_runtime_artifacts(run_parameters)
            schedule_logger(job_id).info(f"task run parameters: {run_parameters}")
            task_executor_process_start_status = False

            config_dir = job_utils.get_task_directory(job_id, role, party_id, task.f_task_name, task_id, task_version)
            os.makedirs(config_dir, exist_ok=True)
            run_parameters_path = os.path.join(config_dir, 'task_parameters.json')
            with open(run_parameters_path, 'w') as fw:
                fw.write(json_dumps(run_parameters))
            backend_engine = build_engine()
            run_info = backend_engine.run(task=task,
                                          run_parameters=run_parameters,
                                          run_parameters_path=run_parameters_path,
                                          config_dir=config_dir,
                                          log_dir=job_utils.get_job_log_directory(job_id, role, party_id,
                                                                                  task.f_task_name),
                                          cwd_dir=job_utils.get_job_directory(job_id, role, party_id, task.f_task_name))
            task_info.update(run_info)
            task_info["start_time"] = current_timestamp()
            task_executor_process_start_status = True
        except Exception as e:
            schedule_logger(job_id).exception(e)
            is_failed = True
        finally:
            try:
                cls.update_task(task_info=task_info)
                task_info["party_status"] = TaskStatus.RUNNING
                cls.update_task_status(task_info=task_info)
                if is_failed:
                    task_info["party_status"] = TaskStatus.FAILED
                    cls.update_task_status(task_info=task_info)
            except Exception as e:
                schedule_logger(job_id).exception(e)
            schedule_logger(job_id).info(
                "task {} {} on {} {} executor subprocess start {}".format(task_id, task_version, role, party_id,
                                                                          "success" if task_executor_process_start_status else "failed"))

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
    def update_task_status(cls, task_info, scheduler_party_id=None):
        if not scheduler_party_id:
            scheduler_party_id = JobSaver.query_task(
                task_id=task_info.get("task_id"),
                task_version=task_info.get("task_version")
            )[0].f_scheduler_party_id
        update_status = JobSaver.update_task_status(task_info=task_info)
        if update_status and EndStatus.contains(task_info.get("status")):
            # ResourceManager.return_task_resource(task_info=task_info)
            cls.clean_task(job_id=task_info["job_id"],
                           task_id=task_info["task_id"],
                           task_version=task_info["task_version"],
                           role=task_info["role"],
                           party_id=task_info["party_id"])
        if "party_status" in task_info:
            report_task_info = {
                "job_id": task_info.get("job_id"),
                "role": task_info.get("role"),
                "party_id": task_info.get("party_id"),
                "task_id": task_info.get("task_id"),
                "task_version": task_info.get("task_version"),
                "status": task_info.get("party_status")
            }
            cls.report_task_to_scheduler(task_info=report_task_info, scheduler_party_id=scheduler_party_id)
        return update_status

    @classmethod
    def report_task_to_scheduler(cls, task_info, scheduler_party_id):
        FederatedScheduler.report_task_to_scheduler(party_id=scheduler_party_id, command_body=task_info)

    @classmethod
    def collect_task(cls, job_id, task_id, task_version, role, party_id):
        tasks = JobSaver.query_task(job_id=job_id, task_id=task_id,  task_version=task_version, role=role,
                                    party_id=party_id)
        if tasks:
            return tasks[0].to_human_model_dict(only_primary_with=cls.INITIATOR_COLLECT_FIELDS)
        else:
            return None

    @classmethod
    def stop_task(cls, task: Task, stop_status):
        kill_status = cls.kill_task(task=task)
        task_info = {
            "job_id": task.f_job_id,
            "task_id": task.f_task_id,
            "task_version": task.f_task_version,
            "role": task.f_role,
            "party_id": task.f_party_id,
            "party_status": stop_status,
            "kill_status": True
        }
        cls.update_task_status(task_info=task_info, scheduler_party_id=task.f_scheduler_party_id)
        cls.update_task(task_info=task_info)
        return kill_status

    @classmethod
    def kill_task(cls, task: Task):
        kill_status = False
        try:
            backend_engine = build_engine()
            if backend_engine:
                backend_engine.kill(task)
            WorkerManager.kill_task_all_workers(task)
        except Exception as e:
            schedule_logger(task.f_job_id).exception(e)
        else:
            kill_status = True
        finally:
            schedule_logger(task.f_job_id).info(
                'task {} {} on {} {} process {} kill {}'.format(task.f_task_id,
                                                                task.f_task_version,
                                                                task.f_role,
                                                                task.f_party_id,
                                                                task.f_run_pid,
                                                                'success' if kill_status else 'failed'))
            return kill_status

    @classmethod
    def clean_task(cls, job_id, task_id, task_version, role, party_id):
        pass
