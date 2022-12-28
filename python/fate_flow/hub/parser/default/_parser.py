import os

import networkx as nx
import copy

from pydantic import BaseModel
from typing import Dict, Union

from ._structures import ComponentSpec, RuntimeInputDefinition, ModelWarehouseChannelSpec, InputChannelSpec, DAGSchema,\
    RuntimeTaskOutputChannelSpec, TaskScheduleSpec, TaskRuntimeInputSpec, IOArtifact, OutputSpec, \
    OutputMetricSpec, OutputModelSpec, OutputDataSpec, MLMDSpec, LOGGERSpec, ComputingBackendSpec, \
    FederationBackendSpec, RuntimeConfSpec

from fate_flow.entity.types import ArtifactSourceType
from fate_flow.manager.output_manager import OutputDataTracking
from fate_flow.operation.job_saver import JobSaver
from fate_flow.runtime.job_default_config import JobDefaultConfig
from fate_flow.settings import ENGINES, LOCAL_DATA_STORE_PATH, BASE_URI
from fate_flow.utils import job_utils
from fate_flow.entity.engine_types import StorageEngine, EngineType
from fate_flow.entity.scheduler_structures import SchedulerInfoSpec
from fate_flow.utils.log_utils import schedule_logger
from .. import TaskParserABC, JobParserABC


class TaskNodeInfo(object):
    def __init__(self):
        self._runtime_parameters = None
        self._runtime_parties = None
        self._input_dependencies = None
        self._component_ref = None
        self._component_spec = None
        self._upstream_inputs = dict()
        self._stage = None
        self._conf = None

    @property
    def stage(self):
        return self._stage

    @stage.setter
    def stage(self, stage):
        self._stage = stage

    @property
    def runtime_parameters(self):
        return self._runtime_parameters

    @runtime_parameters.setter
    def runtime_parameters(self, runtime_parameters):
        self._runtime_parameters = runtime_parameters

    @property
    def runtime_parties(self):
        return self._runtime_parties

    @runtime_parties.setter
    def runtime_parties(self, runtime_parties):
        self._runtime_parties = runtime_parties

    @property
    def upstream_inputs(self):
        return self._upstream_inputs

    @upstream_inputs.setter
    def upstream_inputs(self, upstream_inputs):
        self._upstream_inputs = upstream_inputs

    @property
    def component_spec(self):
        return self._component_spec

    @component_spec.setter
    def component_spec(self, component_spec):
        self._component_spec = component_spec

    @property
    def output_definitions(self):
        return self._component_spec.output_definitions

    @property
    def component_ref(self):
        return self._component_ref

    @component_ref.setter
    def component_ref(self, component_ref):
        self._component_ref = component_ref

    @property
    def conf(self):
        return self._conf

    @conf.setter
    def conf(self, conf):
        self._conf = conf


class TaskParser(TaskParserABC):
    def __init__(self, task_node, job_id, task_name, role, party_id, task_id="", execution_id="",
                 task_version=None, parties=None):
        self.task_node = task_node
        self.job_id = job_id
        self.task_name = task_name
        self.role = role
        self.party_id = party_id
        self.task_id = task_id
        self.task_version = task_version
        self.execution_id = execution_id
        self.parties = parties

    @property
    def need_run(self):
        return (self.role, self.party_id) in [(party.role, party.party_id) for party in self.runtime_parties]

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
    def input_parameters(self):
        return self.task_node.runtime_parameters.get(self.role, {}).get(self.party_id, {})

    @property
    def input_artifacts(self):
        task_artifacts = {}
        if self.task_node.upstream_inputs:
            for k, v in self.task_node.upstream_inputs.items():
                if isinstance(v, dict):
                    task_artifacts[k] = v
                else:
                    _data = self.get_artifacts_data(k, v)
                    if _data:
                        task_artifacts[k] = _data
        return task_artifacts

    def get_model_warehouse_source(self, channel: ModelWarehouseChannelSpec):
        jobs = JobSaver.query_job(model_id=channel.model_id, model_version=channel.model_version, role=self.role, party_id=self.party_id)
        if jobs:
            job_id = jobs[0].f_job_id
            return job_id
        else:
            raise Exception("no found model warehouse")

    def get_artifacts_data(self, name, channel: InputChannelSpec):
        job_id = self.job_id
        if isinstance(channel, ModelWarehouseChannelSpec):
            job_id = self.get_model_warehouse_source(channel)
        data = OutputDataTracking.query(task_name=channel.producer_task, output_key=channel.output_artifact_key,
                                        role=self.role, party_id=self.party_id,  job_id=job_id)
        if data:
            data = data[-1]
            return IOArtifact(name=name, uri=data.f_uri, metadata=data.f_meta).dict()
        return {}

    def generate_task_outputs(self):
        return OutputSpec(
            model=self.get_output_model_store_conf(),
            data=self.get_output_data_store_conf(),
            metric=self.get_output_data_metric_conf(),
        )

    def get_output_model_store_conf(self):
        model_id, model_version = job_utils.generate_model_info(job_id=self.job_id)
        _type = JobDefaultConfig.task_default_conf.get("output").get("model").get("type")
        _format = JobDefaultConfig.task_default_conf.get("output").get("model").get("format")

        return OutputModelSpec(
            type=_type,
            metadata={
                "uri": f"{BASE_URI}/worker/task/model/{self.role}/{self.party_id}/{model_id}/{str(model_version)}/{self.component_ref}/{self.task_name}",
                "format": _format
            }
        )

    def get_output_data_store_conf(self):
        _type = JobDefaultConfig.task_default_conf.get("output").get("data").get("type")
        _format = JobDefaultConfig.task_default_conf.get("output").get("data").get("format")

        if ENGINES.get(EngineType.STORAGE) in [StorageEngine.STANDALONE, StorageEngine.LOCALFS]:
            os.makedirs(os.path.join(LOCAL_DATA_STORE_PATH, self.task_id), exist_ok=True)
            return OutputDataSpec(type=_type, metadata={
                "uri": f"file://{LOCAL_DATA_STORE_PATH}/{self.task_id}",
                "format": _format
            })

    def get_output_data_metric_conf(self):
        _type = JobDefaultConfig.task_default_conf.get("output").get("metric").get("type")
        _format = JobDefaultConfig.task_default_conf.get("output").get("metric").get("format")

        return OutputMetricSpec(
            type=_type,
            metadata={
                "uri": f"{BASE_URI}/worker/task/metric/{self.job_id}/{self.role}/"
                       f"{self.party_id}/{self.task_name}/{self.task_id}/{self.task_version}",
                "format": _format
            })

    @staticmethod
    def generate_mlmd():
        _type = "flow"
        _statu_uri = f"{BASE_URI}/worker/task/report"
        _tracking_uri = f'{BASE_URI}/worker/task/output/tracking'
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
        return ComputingBackendSpec(type=ENGINES.get(EngineType.STORAGE), metadata={"computing_id": self.computing_id})

    def generate_federation_conf(self):
        parties = []
        for party in self.parties:
            for _party_id in party.party_id:
                parties.append({"role": party.role, "partyid": _party_id})
        return FederationBackendSpec(
            type=ENGINES.get(EngineType.STORAGE),
            metadata={
                "federation_id": self.federation_id,
                "parties": {
                    "local": {"role": self.role, "partyid": self.party_id},
                    "parties": parties
                }
            }
        )

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

    @property
    def task_parameters(self) -> TaskScheduleSpec:
        return TaskScheduleSpec(
            taskid=self.execution_id,
            component=self.component_ref,
            role=self.role,
            stage=self.stage,
            party_id=self.party_id,
            inputs=TaskRuntimeInputSpec(parameters=self.input_parameters).dict(),
            conf=self.task_conf
        )

    def update_runtime_artifacts(self, task_parameters):
        task_parameters["inputs"].update({"artifacts": self.input_artifacts})
        schedule_logger(job_id=self.job_id).info(f"update artifacts: {self.input_artifacts}")
        return task_parameters


class JobParser(JobParserABC):
    def __init__(self, dag_conf):
        self._dag = nx.DiGraph()
        self._links = dict()
        self._task_parameters = dict()
        self._task_parties = dict()
        self._tasks = dict()
        self._conf = dict()
        self.parse_dag(dag_schema=dag_conf)

    def parse_dag(self, dag_schema: DAGSchema, component_specs: Dict[str, ComponentSpec] = None):
        dag_spec = dag_schema.dag
        dag_stage = dag_spec.stage
        tasks = dag_spec.tasks
        if dag_spec.conf:
            self._conf = dag_spec.conf.dict(exclude_defaults=True)
        job_conf = self._conf.get("task", {})
        for name, task_spec in tasks.items():
            self._dag.add_node(name)
            task_stage = dag_stage
            component_ref = task_spec.component_ref
            if not task_spec.conf:
                task_conf = copy.deepcopy(job_conf)
            else:
                task_conf = copy.deepcopy(task_spec.conf).update(job_conf)
            if task_spec.stage:
                task_stage = task_spec.stage

            self._tasks[name] = TaskNodeInfo()
            self._tasks[name].stage = task_stage
            self._tasks[name].component_ref = component_ref
            if component_specs:
                self._tasks[name].component_spec = component_specs[name]
            self._init_task_runtime_parameters_and_conf(name, dag_schema, task_conf)

            if not task_spec.inputs or not task_spec.inputs.artifacts:
                continue

            upstream_inputs = dict()
            for input_key, output_specs_dict in task_spec.inputs.artifacts.items():
                upstream_inputs[input_key] = dict()
                for artifact_source, channel_spec_list in output_specs_dict.items():
                    if artifact_source == ArtifactSourceType.MODEL_WAREHOUSE:
                        if isinstance(channel_spec_list, list):
                            inputs = []
                            for channel in channel_spec_list:
                                model_warehouse_channel = ModelWarehouseChannelSpec(**channel.dict(exclude_defaults=True))
                                if model_warehouse_channel.model_id is None:
                                    model_warehouse_channel.model_id = self._conf.get("model_id", None)
                                    model_warehouse_channel.model_version = self._conf.get("model_version", None)
                                inputs.append(model_warehouse_channel)
                        else:
                            inputs = ModelWarehouseChannelSpec(**channel_spec_list.dict(exclude_defaults=True))
                            if inputs.model_id is None:
                                inputs.model_id = self._conf.get("model_id", None)
                                inputs.model_version = self._conf.get("model_version", None)

                        upstream_inputs[input_key] = inputs
                        continue
                    else:
                        if isinstance(channel_spec_list, list):
                            inputs = [RuntimeTaskOutputChannelSpec(**channel.dict(exclude_defaults=True))
                                      for channel in channel_spec_list]
                        else:
                            inputs = RuntimeTaskOutputChannelSpec(**channel_spec_list.dict(exclude_defaults=True))

                        upstream_inputs[input_key] = inputs

                    if not isinstance(channel_spec_list, list):
                        channel_spec_list = [channel_spec_list]

                    for channel_spec in channel_spec_list:
                        dependent_task = channel_spec.producer_task
                        self._add_edge(dependent_task, name)

            self._tasks[name].upstream_inputs = upstream_inputs

    def _add_edge(self, src, dst, attrs=None):
        if not attrs:
            attrs = {}

        self._dag.add_edge(src, dst, **attrs)

    def _init_task_runtime_parameters_and_conf(self, task_name: str, dag_schema: DAGSchema, global_task_conf):
        dag = dag_schema.dag
        role_keys = set([party.role for party in dag.parties])
        task_spec = dag.tasks[task_name]
        if task_spec.parties:
            task_role_keys = set([party.role for party in task_spec.parties])
            role_keys = role_keys & task_role_keys

        common_parameters = dict()
        if task_spec.inputs and task_spec.inputs.parameters:
            common_parameters = task_spec.inputs.parameters

        task_parameters = dict()
        task_conf = dict()
        task_runtime_parties = []

        for party in dag.parties:
            if party.role not in role_keys:
                continue
            task_parameters[party.role] = dict()
            task_conf[party.role] = dict()
            for party_id in party.party_id:
                task_parameters[party.role][party_id] = copy.deepcopy(common_parameters)
                task_conf[party.role][party_id] = copy.deepcopy(global_task_conf)
                task_runtime_parties.append(Party(role=party.role, party_id=party_id))

        if dag.party_tasks:
            party_tasks = dag.party_tasks
            for site_name, party_tasks_spec in party_tasks.items():
                if task_name not in party_tasks_spec.tasks:
                    continue

                party_task_conf = copy.deepcopy(party_tasks_spec.conf) if party_tasks_spec.conf else dict()
                party_task_conf.update(global_task_conf)

                party_parties = party_tasks_spec.parties
                party_task_spec = party_tasks_spec.tasks[task_name]

                if party_task_spec.conf:
                    _conf = copy.deepcopy(party_task_spec.conf)
                    party_task_conf = _conf.update(party_task_conf)
                for party in party_parties:
                    if party.role in task_parameters:
                        for party_id in party.party_id:
                            task_conf[party.role][party_id].update(party_task_conf)

                if not party_task_spec.inputs:
                    continue
                parameters = party_task_spec.inputs.parameters

                if parameters:
                    for party in party_parties:
                        if party.role in task_parameters:
                            for party_id in party.party_id:
                                task_parameters[party.role][party_id].update(parameters)

        self._tasks[task_name].runtime_parameters = task_parameters
        self._tasks[task_name].runtime_parties = task_runtime_parties
        self._tasks[task_name].conf = task_conf

    def get_task_node(self, task_name):
        return self._tasks[task_name]

    def topological_sort(self):
        return nx.topological_sort(self._dag)

    @classmethod
    def infer_dependent_tasks(cls, task_input: RuntimeInputDefinition):
        if not task_input or not task_input.artifacts:
            return []
        dependent_task_list = list()
        for artifact_name, artifact_channel in task_input.artifacts.items():
            for artifact_source_type, channels in artifact_channel.items():
                if artifact_source_type == ArtifactSourceType.MODEL_WAREHOUSE:
                    continue

                if not isinstance(channels, list):
                    channels = [channels]
                for channel in channels:
                    dependent_task_list.append(channel.producer_task)
        return dependent_task_list


class Party(BaseModel):
    role: str
    party_id: Union[str, int]


class DagSchemaParser(object):
    def __init__(self, dag_schema):
        self.dag_schema = DAGSchema(**dag_schema)

    @property
    def job_schedule_info(self) -> SchedulerInfoSpec:
        return SchedulerInfoSpec(
            dag=self.dag_schema.dict(),
            parties=[party.dict() for party in self.dag_schema.dag.parties],
            initiator_party_id=self.dag_schema.dag.conf.initiator_party_id,
            scheduler_party_id=self.dag_schema.dag.conf.scheduler_party_id,
            federated_status_collect_type=self.dag_schema.dag.conf.federated_status_collect_type,
            model_id=self.dag_schema.dag.conf.model_id,
            model_version=self.dag_schema.dag.conf.model_version
        )
