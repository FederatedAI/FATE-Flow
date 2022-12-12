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

from arch import json_dumps, current_timestamp
from fate_flow.db.db_models import Task
from fate_flow.engine.computing import build_engine
from fate_flow.entity.dag_structures import RuntimeOutputChannelSpec, DAGSchema
from fate_flow.entity.task_structures import IOArtifact, TaskRuntimeInputSpec, TaskScheduleSpec, RuntimeConfSpec, \
    OutputSpec, OutputModelSpec, OutputDataSpec, OutputMetricSpec, MLMDSpec, LOGGERSpec, ComputingBackendSpec, \
    FederationBackendSpec
from fate_flow.manager.output_manager import OutputDataTracking
from fate_flow.manager.worker_manager import WorkerManager
from fate_flow.runtime.job_default_config import JobDefaultConfig
from fate_flow.scheduler.dsl_parser import TaskNodeInfo, DagParser
from fate_flow.scheduler.federated_scheduler import FederatedScheduler
from fate_flow.entity.run_status import EndStatus, TaskStatus
from fate_flow.operation.job_saver import JobSaver
from fate_flow.settings import HOST, HTTP_PORT, API_VERSION, DATA_STORE_PATH
from fate_flow.utils import job_utils
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
            dag_parser = DagParser()
            job = JobSaver.query_job(job_id=job_id, role=role, party_id=party_id)[0]
            dag_schema = DAGSchema(**job.f_dag)
            dag_parser.parse_dag(dag_schema=dag_schema)
            task_parser = TaskParser(dag_parser=dag_parser, job_id=job_id, task_name=task.f_task_name, role=role,
                                     party_id=party_id, parties=dag_schema.dag.parties)
            task_parser.update_task_runtime_artifacts(run_parameters)
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


class TaskParser(object):
    def __init__(self, dag_parser, job_id, task_name, role, party_id, task_id="", execution_id="",
                 task_version=None, parties=None):
        self.dag_parser = dag_parser
        self.job_id = job_id
        self.task_name = task_name
        self.role = role
        self.party_id = party_id
        self.task_id = task_id
        self.task_version = task_version
        self.execution_id = execution_id
        self.parties = parties

    @property
    def task_node(self) -> TaskNodeInfo:
        return self.dag_parser.get_task_node(task_name=self.task_name)

    @property
    def federation_id(self):
        return job_utils.generate_task_version_id(task_id=self.task_id, task_version=self.task_version)

    @property
    def computing_id(self):
        return job_utils.generate_session_id(self.task_id, self.task_version, self.role, self.party_id)

    @property
    def runtime_parties(self):
        return self.task_node.runtime_parties

    @property
    def component_ref(self):
        return self.task_node.component_ref

    @property
    def stage(self):
        return self.task_node.stage

    @property
    def runtime_parameters(self):
        return self.task_node.runtime_parameters

    @property
    def output_definitions(self):
        return self.task_node.output_definitions

    @property
    def task_runtime_conf(self):
        return self.task_node.conf

    @property
    def need_run(self):
        return (self.role, self.party_id) in [(party.role, party.party_id) for party in self.runtime_parties]

    @property
    def input_parameters(self):
        return self.task_node.runtime_parameters.get(self.role, {}).get(self.party_id, {})

    @property
    def input_artifacts(self):
        task_artifacts = {}
        if self.task_node.upstream_inputs:
            for k, v in self.task_node.upstream_inputs.items():
                if isinstance(v, dict):
                    task_artifacts[k] = v
                elif isinstance(v, RuntimeOutputChannelSpec):
                    task_artifacts[k] = self.get_artifacts_data(k, v)

        return task_artifacts

    def get_artifacts_data(self, name, channel: RuntimeOutputChannelSpec):
        data = OutputDataTracking.query(task_name=channel.producer_task, output_key=channel.output_artifact_key,
                                        role=self.role, party_id=self.party_id,  job_id=self.job_id)
        if data:
            data = data[-1]
            return IOArtifact(name=name, uri=data.f_uri, metadata=data.f_meta).dict()
        return IOArtifact(name=name, uri="", metadata={}).dict()

    def generate_task_outputs(self):
        return OutputSpec(
            model=self.get_output_model_store_conf(),
            data=self.get_output_data_store_conf(),
            metric=OutputMetricSpec(type="directory", metadata={"uri": "", "format": "json"}),
        )

    def get_output_model_store_conf(self):
        model_conf = deepcopy(JobDefaultConfig.task_default_conf.get("output", {}).get("model", {}))
        if model_conf.get("metadata"):
            uri = model_conf["metadata"].get("uri").replace("task_name", self.task_name).replace("model_id", self.job_id).replace("model_version", "0")
            model_conf["metadata"]["uri"] = f'http://{HOST}:{HTTP_PORT}/{API_VERSION}{uri}'
        return OutputModelSpec(**model_conf)

    def get_output_data_store_conf(self):
        data_conf = deepcopy(JobDefaultConfig.task_default_conf.get("output", {}).get("data", {}))
        os.makedirs(DATA_STORE_PATH, exist_ok=True)
        return OutputDataSpec(type="directory", metadata={"uri": DATA_STORE_PATH, "format": "dataframe"})

    @staticmethod
    def generate_mlmd():
        _type = JobDefaultConfig.task_default_conf.get("mlmd", {}).get("type")
        _statu_uri = f'http://{HOST}:{HTTP_PORT}/{API_VERSION}{JobDefaultConfig.task_default_conf.get("mlmd", {}).get("metadata", {}).get("statu_uri", "")}'
        _tracking_uri = f'http://{HOST}:{HTTP_PORT}/{API_VERSION}{JobDefaultConfig.task_default_conf.get("mlmd", {}).get("metadata", {}).get("tracking_uri", "")}'
        return MLMDSpec(
            type=_type,
            metadata={
                "statu_uri": _statu_uri,
                "tracking_uri": _tracking_uri
            })

    def generate_logger_conf(self):
        logger_conf = JobDefaultConfig.task_default_conf.get("logger")
        log_dir = job_utils.get_job_log_directory(self.job_id, self.role, self.party_id, self.task_name)
        if logger_conf.get("metadata"):
            logger_conf.get("metadata").update({"basepath": log_dir})
        return LOGGERSpec(**logger_conf)

    @staticmethod
    def generate_device():
        return JobDefaultConfig.task_default_conf.get("device")

    def generate_computing_conf(self):
        return ComputingBackendSpec(type="standalone", metadata={"computing_id": self.computing_id})

    def generate_federation_conf(self):
        parties = []
        for party in self.parties:
            for _party_id in party.party_id:
                if _party_id != self.party_id and party.role != self.role:
                    parties.append({"role": party.role, "partyid": _party_id})
        return FederationBackendSpec(type="standalone", metadata={"federation_id": self.federation_id, "parties": {
            "local": {"role": self.role, "partyid": self.party_id},
            "parties": parties
        }})

    @property
    def task_conf(self):
        return RuntimeConfSpec(
            output=self.generate_task_outputs(),
            mlmd=self.generate_mlmd(),
            logger=self.generate_logger_conf(),
            device=self.generate_device(),
            computing=self.generate_computing_conf(),
            federation=self.generate_federation_conf()
        )

    def get_task_parameters(self) -> TaskScheduleSpec:
        return TaskScheduleSpec(
            taskid=self.execution_id,
            component=self.component_ref,
            role=self.role,
            stage=self.stage,
            party_id=self.party_id,
            inputs=TaskRuntimeInputSpec(parameters=self.input_parameters).dict(),
            conf=self.task_conf
        )

    def update_task_runtime_artifacts(self, task_parameters):
        task_parameters["inputs"].update({"artifacts": self.input_artifacts})
        return task_parameters
