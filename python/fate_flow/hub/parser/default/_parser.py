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
import os

import networkx as nx
import copy

from pydantic import BaseModel
from typing import Dict, Union, List

from fate_flow.manager.service.provider_manager import ProviderManager
from ._federation import StandaloneFederationSpec, RollSiteFederationSpec, OSXFederationSpec, PulsarFederationSpec, \
    RabbitMQFederationSpec
from fate_flow.entity.spec import ComponentSpec, RuntimeInputDefinition, ModelWarehouseChannelSpec, InputChannelSpec, \
    DAGSchema, RuntimeTaskOutputChannelSpec, TaskArtifactSpec, TaskConfigSpec, MLMDSpec, \
    FlowLogger, ComputingBackendSpec

from fate_flow.manager.service.output_manager import OutputDataTracking
from fate_flow.operation.job_saver import JobSaver
from fate_flow.runtime.job_default_config import JobDefaultConfig
from fate_flow.runtime.system_settings import ENGINES, BASE_URI, PROXY, FATE_FLOW_CONF_PATH, HOST, HTTP_PORT, PROTOCOL, \
    API_VERSION
from fate_flow.utils import job_utils, file_utils
from fate_flow.entity.types import EngineType, FederationEngine, DataSet
from fate_flow.entity.spec import SchedulerInfoSpec
from fate_flow.utils.log_utils import schedule_logger
from .. import TaskParserABC, JobParserABC


class ArtifactSourceType(object):
    TASK_OUTPUT_ARTIFACT = "task_output_artifact"
    MODEL_WAREHOUSE = "model_warehouse"


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
    def runtime_roles(self) -> list:
        roles = set()
        for party_spec in self._runtime_parties:
            roles.add(party_spec.role)

        return list(roles)

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
                 task_version=None, parties=None, provider=None):
        self.task_node = task_node
        self.job_id = job_id
        self.task_name = task_name
        self.role = role
        self.party_id = party_id
        self.task_id = task_id
        self.task_version = task_version
        self.execution_id = execution_id
        self.parties = parties
        self._provider = None

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
        _rc = self.task_node.conf.get(self.role, {}).get(self.party_id, {})
        return _rc if _rc else {}

    @property
    def provider(self):
        if not self._provider:
            provider_name = self.task_runtime_conf.get("provider")
            self._provider = ProviderManager.check_provider_name(provider_name)
        return self._provider

    @property
    def provider_name(self):
        return ProviderManager.parser_provider_name(self.provider)[0]

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
            return TaskArtifactSpec(name=name, uri=data.f_uri, metadata=data.f_meta).dict()
        return {}

    @staticmethod
    def generate_mlmd():
        _type = "flow"
        return MLMDSpec(
            type=_type,
            metadata={
                "host": HOST,
                "port": HTTP_PORT,
                "protocol": PROTOCOL,
                "api_version": API_VERSION
            })

    def generate_logger_conf(self):
        logger_conf = JobDefaultConfig.task_default_conf.get("logger")
        log_dir = job_utils.get_job_log_directory(self.job_id, self.role, self.party_id, self.task_name)
        if logger_conf.get("metadata"):
            logger_conf.get("metadata").update({"basepath": log_dir})
        return FlowLogger(**logger_conf)

    @staticmethod
    def generate_device():
        return JobDefaultConfig.task_default_conf.get("device")

    def generate_computing_conf(self):
        return ComputingBackendSpec(type=ENGINES.get(EngineType.COMPUTING).lower(), metadata={"computing_id": self.computing_id})

    def generate_federation_conf(self):
        parties_info = []
        for party in self.parties:
            for _party_id in party.party_id:
                parties_info.append({"role": party.role, "partyid": _party_id})
        parties = {
            "local": {"role": self.role, "partyid": self.party_id},
            "parties": parties_info
        }
        engine_name = ENGINES.get(EngineType.FEDERATION).lower()
        proxy_conf = PROXY.get(engine_name, {})
        if engine_name == FederationEngine.STANDALONE:
            spec = StandaloneFederationSpec(type=engine_name, metadata=StandaloneFederationSpec.MetadataSpec(
                federation_id=self.federation_id, parties=parties))
        elif engine_name == FederationEngine.ROLLSITE:
            spec = RollSiteFederationSpec(type=engine_name, metadata=RollSiteFederationSpec.MetadataSpec(
                federation_id=self.federation_id,
                parties=parties,
                rollsite_config=RollSiteFederationSpec.MetadataSpec.RollSiteConfig(**proxy_conf)
            ))
        elif engine_name == FederationEngine.OSX:
            spec = OSXFederationSpec(type=engine_name, metadata=OSXFederationSpec.MetadataSpec(
                federation_id=self.federation_id,
                parties=parties,
                osx_config=OSXFederationSpec.MetadataSpec.OSXConfig(**proxy_conf)
            ))
        elif engine_name == FederationEngine.PULSAR:
            route_table_path = os.path.join(FATE_FLOW_CONF_PATH, "pulsar_route_table.yaml")
            route_table = file_utils.load_yaml_conf(conf_path=route_table_path)

            spec = PulsarFederationSpec(type=engine_name, metadata=PulsarFederationSpec.MetadataSpec(
                federation_id=self.federation_id,
                parties=parties,
                route_table=PulsarFederationSpec.MetadataSpec.RouteTable(
                    route={k: PulsarFederationSpec.MetadataSpec.RouteTable.Route(**v) for k, v in route_table.items() if k!= "default"},
                    default=PulsarFederationSpec.MetadataSpec.RouteTable.Default(**route_table.get("default", {})) if route_table.get("default") else None
                ),
                pulsar_config=PulsarFederationSpec.MetadataSpec.PulsarConfig(**proxy_conf)
            ))
        elif engine_name == FederationEngine.RABBITMQ:
            route_table_path = os.path.join(FATE_FLOW_CONF_PATH, "rabbitmq_route_table.yaml")
            route_table = file_utils.load_yaml_conf(conf_path=route_table_path)
            spec = RabbitMQFederationSpec(type=engine_name, metadata=RabbitMQFederationSpec.MetadataSpec(
                federation_id=self.federation_id,
                parties=parties,
                route_table={k: RabbitMQFederationSpec.MetadataSpec.RouteTable(**v) for k, v in route_table.items()},
                rabbitmq_config=RabbitMQFederationSpec.MetadataSpec.RabbitMQConfig(**proxy_conf)
            ))
        else:
            raise RuntimeError(f"federation engine {engine_name} is not supported")
        return spec

    @property
    def task_conf(self):
        return TaskConfigSpec.TaskConfSpec(
            mlmd=self.generate_mlmd(),
            logger=self.generate_logger_conf(),
            device=self.generate_device(),
            computing=self.generate_computing_conf(),
            federation=self.generate_federation_conf()
        )

    @property
    def task_parameters(self) -> TaskConfigSpec:
        return TaskConfigSpec(
            model_id="",
            model_version="",
            job_id=self.job_id,
            task_id=self.task_id,
            task_version=self.task_version,
            task_name=self.task_name,
            provider_name=self.provider_name,
            party_task_id=self.execution_id,
            component=self.component_ref,
            role=self.role,
            stage=self.stage,
            party_id=self.party_id,
            inputs=TaskConfigSpec.TaskInputsSpec(parameters=self.input_parameters, artifacts=self.task_node.upstream_inputs).dict(),
            conf=self.task_conf
        )

    def update_runtime_artifacts(self, task_parameters):
        # update runtime artifacts: input model and data
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
                task_conf = copy.deepcopy(job_conf).update(task_spec.conf)
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
            runtime_roles = self._tasks[name].runtime_roles
            for input_key, output_specs_dict in task_spec.inputs.artifacts.items():
                upstream_inputs[input_key] = dict()
                for artifact_source, channel_spec_list in output_specs_dict.items():
                    if artifact_source == ArtifactSourceType.MODEL_WAREHOUSE:
                        if isinstance(channel_spec_list, list):
                            inputs = []
                            for channel in channel_spec_list:
                                model_warehouse_channel = ModelWarehouseChannelSpec(**channel.dict(exclude_defaults=True))
                                if model_warehouse_channel.model_id is None:
                                    model_warehouse_channel.model_id = \
                                        self._conf.get("model_warehouse", {}).get("model_id", None)
                                    model_warehouse_channel.model_version = \
                                        self._conf.get("model_warehouse", {}).get("model_version", None)
                                inputs.append(model_warehouse_channel)
                        else:
                            inputs = ModelWarehouseChannelSpec(**channel_spec_list.dict(exclude_defaults=True))
                            if inputs.model_id is None:
                                inputs.model_id = self._conf.get("model_warehouse", {}).get("model_id", None)
                                inputs.model_version = self._conf.get("model_warehouse", {}).get("model_version", None)

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

            upstream_inputs = self.check_and_add_runtime_roles(upstream_inputs, runtime_roles)
            self._tasks[name].upstream_inputs = upstream_inputs

    @staticmethod
    def check_and_add_runtime_roles(upstream_inputs, runtime_roles):
        correct_inputs = copy.deepcopy(upstream_inputs)
        for input_key, channel_list in upstream_inputs.items():
            if isinstance(channel_list, list):
                for idx, channel in enumerate(channel_list):
                    if channel.roles is None:
                        correct_inputs[input_key][idx].roles = runtime_roles
            else:
                if channel_list.roles is None:
                    correct_inputs[input_key].roles = runtime_roles

        return correct_inputs

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

    @property
    def task_parser(self):
        return TaskParser

    @property
    def component_ref_list(self):
        _list = []
        for name in self.topological_sort():
            node = self.get_task_node(name)
            if node:
                _list.append(node.component_ref)
        return _list

    def dataset_list(self, role, party_id) -> List[DataSet]:
        _list = []
        for task_name in self.topological_sort():
            task_node = self.get_task_node(task_name)
            if task_node.component_ref == "reader":
                name = task_node.runtime_parameters.get(role, {}).get(party_id, {}).get("name", "")
                namespace = task_node.runtime_parameters.get(role, {}).get(party_id, {}).get("name", "namespace")
                if name and namespace:
                    _list.append(DataSet(**{
                        "name": name,
                        "namespace": namespace
                    }))
        return _list

    def role_parameters(self, role, party_id):
        _dict = {}
        for task_name in self.topological_sort():
            task_node = self.get_task_node(task_name)
            _dict[task_node.component_ref] = task_node.runtime_parameters.get(role, {}).get(party_id, {})
        return _dict


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
            federated_status_collect_type=self.dag_schema.dag.conf.sync_type,
            model_id=self.dag_schema.dag.conf.model_id,
            model_version=self.dag_schema.dag.conf.model_version
        )
