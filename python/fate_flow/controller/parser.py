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
import copy
import logging
import os
from typing import Dict, Union, List

import networkx as nx
from pydantic import BaseModel

from fate_flow.entity.spec.dag import DataWarehouseChannelSpec, ModelWarehouseChannelSpec, \
    RuntimeTaskOutputChannelSpec, ComponentSpec, EggrollComputingSpec, SparkComputingSpec, StandaloneComputingSpec, \
    StandaloneFederationSpec, RollSiteFederationSpec, OSXFederationSpec, \
    PulsarFederationSpec, RabbitMQFederationSpec, FlowLogger, MLMDSpec, TaskRuntimeConfSpec, \
    DAGSchema, DAGSpec, PreTaskConfigSpec, FlowRuntimeInputArtifacts, OutputArtifactType, PartySpec
from fate_flow.entity.types import EngineType, FederationEngine, DataSet, InputArtifactType, ArtifactSourceType, \
    ComputingEngine, OSXMode
from fate_flow.manager.service.provider_manager import ProviderManager
from fate_flow.runtime.job_default_config import JobDefaultConfig
from fate_flow.runtime.system_settings import ENGINES, PROXY, FATE_FLOW_CONF_PATH, HOST, HTTP_PORT, PROTOCOL, \
    API_VERSION, COMPUTING_CONF, LOG_LEVEL
from fate_flow.utils import job_utils, file_utils


class TaskNodeInfo(object):
    def __init__(self):
        self._runtime_parameters = None
        self._runtime_parties = None
        self._input_dependencies = None
        self._component_ref = None
        self._component_spec = None
        self._upstream_inputs = dict()
        self._outputs = dict()
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
    def outputs(self):
        return self._outputs

    @outputs.setter
    def outputs(self, outputs):
        self._outputs = outputs

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


class TaskParser(object):
    def __init__(self, task_node, job_id, task_name, role=None, party_id=None, task_id="", execution_id="", model_id="",
                 model_version="", task_version=None, parties=None, component=None, provider=None, **kwargs):
        self.task_node = task_node
        self.model_id = model_id
        self.model_version = model_version
        self.job_id = job_id
        self.task_name = task_name
        self.role = role
        self.party_id = party_id
        self.task_id = task_id
        self.task_version = task_version
        self.execution_id = execution_id
        self.parties = parties
        self._provider = None
        self.component = component

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
        return self.component if self.component else self.task_node.component_ref

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
        _rc = self.task_node.conf
        return _rc if _rc else {}

    @property
    def task_runtime_launcher(self):
        return self.task_runtime_conf.get("launcher_name", "default")

    @property
    def env_vars(self):
        return self.task_runtime_conf.get("env_vars", {})

    @property
    def engine_run(self):
        return self.task_runtime_conf.get("engine_run", {})

    @property
    def provider(self):
        if not self._provider:
            provider_name = self.task_runtime_conf.get("provider")
            self._provider = ProviderManager.check_provider_name(provider_name)
        return self._provider

    @property
    def timeout(self):
        return self.task_runtime_conf.get("timeout", JobDefaultConfig.task_timeout)

    @property
    def provider_name(self):
        return ProviderManager.parser_provider_name(self.provider)[0]

    @property
    def input_parameters(self):
        return self.task_node.runtime_parameters

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
        task_log_dir = job_utils.get_job_log_directory(self.job_id, self.role, self.party_id, self.task_name)
        job_party_log_dir = job_utils.get_job_log_directory(self.job_id, self.role, self.party_id)
        delay = True
        formatters = None
        return FlowLogger.create(task_log_dir=task_log_dir,
                                 job_party_log_dir=job_party_log_dir,
                                 level=logging.getLevelName(LOG_LEVEL),
                                 delay=delay,
                                 formatters=formatters)

    @staticmethod
    def generate_device():
        return JobDefaultConfig.task_device

    def generate_computing_conf(self):
        if ENGINES.get(EngineType.COMPUTING).lower() == ComputingEngine.STANDALONE:
            from fate_flow.runtime.system_settings import STANDALONE_DATA_HOME
            return StandaloneComputingSpec(
                type=ENGINES.get(EngineType.COMPUTING).lower(),
                metadata={"computing_id": self.computing_id, "options": {"data_dir": STANDALONE_DATA_HOME}}
            )

        if ENGINES.get(EngineType.COMPUTING).lower() == ComputingEngine.EGGROLL:
            return EggrollComputingSpec(
                type=ENGINES.get(EngineType.COMPUTING).lower(),
                metadata={
                    "computing_id": self.computing_id,
                    "host": COMPUTING_CONF.get(ComputingEngine.EGGROLL).get("host"),
                    "port": COMPUTING_CONF.get(ComputingEngine.EGGROLL).get("port")
                }
            )

        if ENGINES.get(EngineType.COMPUTING).lower() == ComputingEngine.SPARK:
            return SparkComputingSpec(
                type=ENGINES.get(EngineType.COMPUTING).lower(),
                metadata={
                    "computing_id": self.computing_id,
                    "options": {"home": COMPUTING_CONF.get(ComputingEngine.SPARK).get("home")}
                }
            )

    @staticmethod
    def generate_storage_conf():
        return ENGINES.get(EngineType.STORAGE).lower()

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
        proxy_conf = copy.deepcopy(PROXY.get(engine_name, {}))
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
            mode = proxy_conf.pop("mode", OSXMode.QUEUE)
            if mode == OSXMode.QUEUE:
                spec = OSXFederationSpec(type=engine_name, metadata=OSXFederationSpec.MetadataSpec(
                    federation_id=self.federation_id,
                    parties=parties,
                    osx_config=OSXFederationSpec.MetadataSpec.OSXConfig(**proxy_conf)
                ))
            elif mode == OSXMode.STREAM:
                spec = RollSiteFederationSpec(
                    type=FederationEngine.ROLLSITE,
                    metadata=RollSiteFederationSpec.MetadataSpec(
                        federation_id=self.federation_id,
                        parties=parties,
                        rollsite_config=RollSiteFederationSpec.MetadataSpec.RollSiteConfig(**proxy_conf)
                ))
            else:
                raise RuntimeError(f"federation engine {engine_name} mode {mode}is not supported")
        elif engine_name == FederationEngine.PULSAR:
            route_table_path = os.path.join(FATE_FLOW_CONF_PATH, "pulsar_route_table.yaml")
            route_table = file_utils.load_yaml_conf(conf_path=route_table_path)

            spec = PulsarFederationSpec(type=engine_name, metadata=PulsarFederationSpec.MetadataSpec(
                federation_id=self.federation_id,
                parties=parties,
                route_table=PulsarFederationSpec.MetadataSpec.RouteTable(
                    route={k: PulsarFederationSpec.MetadataSpec.RouteTable.Route(**v) for k, v in route_table.items() if
                           k != "default"},
                    default=PulsarFederationSpec.MetadataSpec.RouteTable.Default(
                        **route_table.get("default", {})) if route_table.get("default") else None
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
        return TaskRuntimeConfSpec(
            logger=self.generate_logger_conf(),
            device=self.generate_device(),
            computing=self.generate_computing_conf(),
            federation=self.generate_federation_conf(),
            storage=self.generate_storage_conf()
        )

    @property
    def task_parameters(self) -> PreTaskConfigSpec:
        return PreTaskConfigSpec(
            model_id=self.model_id,
            model_version=self.model_version,
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
            parameters=self.input_parameters,
            input_artifacts=self.task_node.upstream_inputs,
            conf=self.task_conf,
            mlmd=self.generate_mlmd(),
            env_vars=self.env_vars
        )


class DagParser(object):
    def __init__(self):
        self._dag = dict()
        self._global_dag = nx.DiGraph()
        self._links = dict()
        self._task_parameters = dict()
        self._task_parties = dict()
        self._tasks = dict()
        self._task_runtime_parties = dict()
        self._conf = dict()

    def parse_dag(self, dag_schema: DAGSchema, component_specs: Dict[str, ComponentSpec] = None):
        dag_spec = dag_schema.dag
        dag_stage = dag_spec.stage
        tasks = dag_spec.tasks
        if dag_spec.conf:
            self._conf = dag_spec.conf.dict(exclude_defaults=True)
        job_conf = self._conf.get("task", {})

        for party in dag_spec.parties:
            if party.role not in self._dag:
                self._dag[party.role] = dict()
            for party_id in party.party_id:
                self._dag[party.role][party_id] = nx.DiGraph()

        for name, task_spec in tasks.items():
            parties = task_spec.parties if task_spec.parties else dag_spec.parties
            task_stage = dag_stage
            component_ref = task_spec.component_ref
            if task_spec.stage:
                task_stage = task_spec.stage

            self._global_dag.add_node(name, component_ref=component_ref)

            self._task_runtime_parties[name] = parties

            for party_spec in parties:
                if party_spec.role not in self._tasks:
                    self._tasks[party_spec.role] = dict()
                for party_id in party_spec.party_id:
                    self._dag[party_spec.role][party_id].add_node(name)
                    if party_id not in self._tasks[party_spec.role]:
                        self._tasks[party_spec.role][party_id] = dict()
                    self._tasks[party_spec.role][party_id].update({
                        name: TaskNodeInfo()
                    })
                    self._tasks[party_spec.role][party_id][name].stage = task_stage
                    self._tasks[party_spec.role][party_id][name].component_ref = component_ref
                    if component_specs:
                        self._tasks[party_spec.role][party_id][name].component_spec = component_specs[name]

        for name, task_spec in tasks.items():
            if not task_spec.conf:
                task_conf = copy.deepcopy(job_conf)
            else:
                task_conf = copy.deepcopy(job_conf)
                task_conf.update(task_spec.conf)

            self._init_task_runtime_parameters_and_conf(name, dag_schema, task_conf)

            self._init_upstream_inputs(name, dag_schema.dag)
            self._init_outputs(name, dag_schema.dag)

    def _init_upstream_inputs(self, name, dag: DAGSpec):
        task_spec = dag.tasks[name]
        upstream_inputs = dict()

        parties = task_spec.parties if task_spec.parties else dag.parties
        for party in parties:
            if party.role not in upstream_inputs:
                upstream_inputs[party.role] = dict()
            for party_id in party.party_id:
                self._tasks[party.role][party_id][name].upstream_inputs = self._get_upstream_inputs(
                    name, task_spec, party.role, party_id
                )

    def _get_upstream_inputs(self, name, task_spec, role, party_id):
        upstream_inputs = dict()
        runtime_parties = task_spec.parties

        if runtime_parties:
            runtime_parties_dict = dict((party.role, party.party_id) for party in runtime_parties)
            if role not in runtime_parties_dict or party_id not in runtime_parties_dict[role]:
                return upstream_inputs

        input_artifacts = task_spec.inputs

        if not input_artifacts:
            return upstream_inputs

        for input_type in InputArtifactType.types():
            artifacts = getattr(input_artifacts, input_type)
            if not artifacts:
                continue

            for input_key, output_specs_dict in artifacts.items():
                for artifact_source, channel_spec_list in output_specs_dict.items():
                    if artifact_source == ArtifactSourceType.MODEL_WAREHOUSE:
                        is_list = True
                        if not isinstance(channel_spec_list, list):
                            is_list = False
                            channel_spec_list = [channel_spec_list]
                        inputs = []
                        for channel in channel_spec_list:
                            model_warehouse_channel = ModelWarehouseChannelSpec(**channel.dict(exclude_defaults=True))
                            if model_warehouse_channel.parties and not self.task_can_run(
                                    role, party_id, runtime_parties=model_warehouse_channel.parties):
                                continue

                            if model_warehouse_channel.model_id is None:
                                model_warehouse_channel.model_id = \
                                    self._conf.get("model_warehouse", {}).get("model_id", None)
                                model_warehouse_channel.model_version = \
                                    self._conf.get("model_warehouse", {}).get("model_version", None)
                            inputs.append(model_warehouse_channel)

                        if not inputs:
                            continue

                        if input_type not in upstream_inputs:
                            upstream_inputs[input_type] = dict()

                        if is_list and len(inputs) == 1:
                            is_list = False
                        upstream_inputs[input_type][input_key] = inputs if is_list else inputs[0]
                    elif artifact_source == ArtifactSourceType.DATA_WAREHOUSE:
                        is_list = True
                        if not isinstance(channel_spec_list, list):
                            is_list = False
                            channel_spec_list = [channel_spec_list]
                        inputs = []
                        for channel in channel_spec_list:
                            if channel.parties and \
                                    not self.task_can_run(role, party_id, runtime_parties=channel.parties):
                                continue
                            inputs.append(DataWarehouseChannelSpec(**channel.dict(exclude_defaults=True)))

                        if not inputs:
                            continue
                        if input_type not in upstream_inputs:
                            upstream_inputs[input_type] = dict()

                        if is_list and len(inputs) == 1:
                            is_list = False
                        upstream_inputs[input_type][input_key] = inputs if is_list else inputs[0]
                    else:
                        if not isinstance(channel_spec_list, list):
                            channel_spec_list = [channel_spec_list]

                        filter_channel_spec_list = []
                        for channel_spec in channel_spec_list:
                            if channel_spec.parties:
                                parties_dict = dict((party.role, party.party_id) for party in channel_spec.parties)
                                if role not in parties_dict or party_id not in parties_dict[role]:
                                    continue
                            else:
                                if channel_spec.producer_task not in self._dag[role][party_id].nodes:
                                    continue
                            filter_channel_spec_list.append(channel_spec)

                        if not filter_channel_spec_list:
                            continue

                        if len(filter_channel_spec_list) > 1:
                            inputs = [RuntimeTaskOutputChannelSpec(**channel.dict(exclude_defaults=True))
                                      for channel in filter_channel_spec_list]
                        else:
                            inputs = RuntimeTaskOutputChannelSpec(**filter_channel_spec_list[0].dict(exclude_defaults=True))

                        if not inputs:
                            continue

                        if input_type not in upstream_inputs:
                            upstream_inputs[input_type] = dict()
                        upstream_inputs[input_type][input_key] = inputs

                        for channel_spec in filter_channel_spec_list:
                            dependent_task = channel_spec.producer_task
                            self._add_edge(dependent_task, name, role, party_id)

        upstream_inputs = self.check_and_add_runtime_party(upstream_inputs, role, party_id, artifact_type="input")

        return upstream_inputs

    def _init_outputs(self, name, dag: DAGSpec):
        task_spec = dag.tasks[name]

        if not task_spec.outputs:
            return

        parties = task_spec.parties if task_spec.parties else dag.parties

        for output_type, outputs_dict in iter(task_spec.outputs):
            if not outputs_dict:
                continue

            for outputs_key, output_artifact in outputs_dict.items():
                output_parties = output_artifact.parties if output_artifact.parties else parties
                for party_spec in output_parties:
                    for party_id in party_spec.party_id:
                        if not self.task_can_run(party_spec.role, party_id, runtime_parties=parties):
                            continue

                        if outputs_key not in self._tasks[party_spec.role][party_id][name].outputs:
                            self._tasks[party_spec.role][party_id][name].outputs[output_type] = dict()

                        self._tasks[party_spec.role][party_id][name].outputs[output_type][outputs_key] = output_artifact

        for party_spec in parties:
            for party_id in party_spec.party_id:
                self._tasks[party_spec.role][party_id][name].outputs = self.check_and_add_runtime_party(
                    self._tasks[party_spec.role][party_id][name].outputs,
                    party_spec.role,
                    party_id,
                    artifact_type="output"
                )

    def _add_edge(self, src, dst, role, party_id, attrs=None):
        if not attrs:
            attrs = {}

        self._dag[role][party_id].add_edge(src, dst, **attrs)
        self._global_dag.add_edge(src, dst, **attrs)

    def _init_task_runtime_parameters_and_conf(self, task_name: str, dag_schema: DAGSchema, global_task_conf):
        dag = dag_schema.dag
        task_spec = dag.tasks[task_name]

        common_parameters = dict()
        if task_spec.parameters:
            common_parameters = task_spec.parameters

        parties = dag.parties if not task_spec.parties else task_spec.parties

        for party in parties:
            for party_id in party.party_id:
                self._tasks[party.role][party_id][task_name].runtime_parameters = copy.deepcopy(common_parameters)
                self._tasks[party.role][party_id][task_name].conf = copy.deepcopy(global_task_conf)

        if dag.party_tasks:
            party_tasks = dag.party_tasks
            for site_name, party_tasks_spec in party_tasks.items():
                if party_tasks_spec.conf:
                    for party in party_tasks_spec.parties:
                        for party_id in party.party_id:
                            self._tasks[party.role][party_id][task_name].conf.update(party_tasks_spec.conf)

                if not party_tasks_spec.tasks or task_name not in party_tasks_spec.tasks:
                    continue

                party_parties = party_tasks_spec.parties
                party_task_spec = party_tasks_spec.tasks[task_name]

                if party_task_spec.conf:
                    for party in party_parties:
                        for party_id in party.party_id:
                            self._tasks[party.role][party_id][task_name].conf.update(party_task_spec.conf)

                parameters = party_task_spec.parameters

                if parameters:
                    for party in party_parties:
                        for party_id in party.party_id:
                            self._tasks[party.role][party_id][task_name].runtime_parameters.update(parameters)

    def get_runtime_roles_on_party(self, task_name, party_id):
        task_runtime_parties = self._task_runtime_parties[task_name]

        runtime_roles = set()
        for party_spec in task_runtime_parties:
            if party_id in party_spec.party_id:
                runtime_roles.add(party_spec.role)

        return list(runtime_roles)

    def get_task_node(self, role, party_id, task_name):
        if role not in self._tasks:
            raise ValueError(f"role={role} does ont exist in dag")
        if party_id not in self._tasks[role]:
            raise ValueError(f"role={role}, party_id={party_id} does not exist in dag")
        if task_name not in self._tasks[role][party_id]:
            raise ValueError(f"role={role}, party_id={party_id} does not has task {task_name}")

        return self._tasks[role][party_id][task_name]

    def get_need_revisit_tasks(self, visited_tasks, failed_tasks, role, party_id):
        """
        visited_tasks: already visited tasks
        failed_tasks: failed tasks

        this function finds tasks need to rerun, a task need to rerun if is upstreams is failed
        """
        invalid_tasks = set(self.party_topological_sort(role, party_id)) - set(visited_tasks)
        invalid_tasks |= set(failed_tasks)

        revisit_tasks = []
        for task_to_check in visited_tasks:
            if task_to_check in invalid_tasks:
                revisit_tasks.append(task_to_check)
                continue

            task_valid = True
            task_stack = {task_to_check}
            stack = [task_to_check]

            while len(stack) > 0 and task_valid:
                task = stack.pop()
                pre_tasks = self.party_predecessors(role, party_id, task)

                for pre_task in pre_tasks:
                    if pre_task in task_stack:
                        continue
                    if pre_task in invalid_tasks:
                        task_valid = False
                        break

                    task_stack.add(pre_task)
                    stack.append(pre_task)

            if not task_valid:
                revisit_tasks.append(task_to_check)

        return revisit_tasks

    def topological_sort(self, role, party_id):
        return nx.topological_sort(self._dag[role][party_id])

    def global_topological_sort(self):
        return nx.topological_sort(self._global_dag)

    def get_component_ref(self, task_name):
        return self._global_dag.nodes[task_name]["component_ref"]

    def party_topological_sort(self, role, party_id):
        assert role in self._dag or party_id in self._dag[role], f"role={role}, party_id={party_id} does not exist"
        return nx.topological_sort(self._dag[role][party_id])

    def party_predecessors(self, role, party_id, task):
        return set(self._dag[role][party_id].predecessors(task))

    def party_successors(self, role, party_id, task):
        return self._dag[role][party_id].successors(task)

    def get_edge_attr(self, role, party_id, src, dst):
        return self._dag[role][party_id].edges[src, dst]

    @classmethod
    def task_can_run(cls, role, party_id, component_spec: ComponentSpec=None, runtime_parties: List[PartySpec]=None):
        if component_spec and role not in component_spec.roles:
            return False

        for party_spec in runtime_parties:
            if role == party_spec.role and party_id in party_spec.party_id:
                return True

        return False

    @staticmethod
    def check_and_add_runtime_party(artifacts, role, party_id, artifact_type):
        correct_artifacts = copy.deepcopy(artifacts)
        if artifact_type == "input":
            types = InputArtifactType.types()
        else:
            types = OutputArtifactType.types()

        for t in types:
            if t not in artifacts:
                continue
            for _key, channel_list in artifacts[t].items():
                if isinstance(channel_list, list):
                    for idx, channel in enumerate(channel_list):
                        correct_artifacts[t][_key][idx].parties = [PartySpec(role=role, party_id=[party_id])]
                else:
                    correct_artifacts[t][_key].parties = [PartySpec(role=role, party_id=[party_id])]

        return correct_artifacts

    @property
    def conf(self):
        return self._conf

    @property
    def task_runtime_parties(self):
        return self._task_runtime_parties

    def get_task_runtime_parties(self, task_name):
        return self._task_runtime_parties[task_name]

    @classmethod
    def infer_dependent_tasks(cls, input_artifacts):
        if not input_artifacts:
            return []

        dependent_task_list = list()
        for input_type in InputArtifactType.types():
            artifacts = getattr(input_artifacts, input_type)
            if not artifacts:
                continue
            for artifact_name, artifact_channel in artifacts.items():
                for artifact_source_type, channels in artifact_channel.items():
                    if artifact_source_type in [ArtifactSourceType.MODEL_WAREHOUSE, ArtifactSourceType.DATA_WAREHOUSE]:
                        continue

                    if not isinstance(channels, list):
                        channels = [channels]
                    for channel in channels:
                        dependent_task_list.append(channel.producer_task)

        return dependent_task_list

    @classmethod
    def translate_dag(cls, src, dst, adapter_map, *args, **kwargs):
        translate_func = adapter_map[src][dst]
        return translate_func(*args, **kwargs)


class JobParser(object):
    def __init__(self, dag_conf):
        self.dag_parser = DagParser()
        self.dag_parser.parse_dag(dag_conf)

    def get_task_node(self, role, party_id, task_name):
        return self.dag_parser.get_task_node(role, party_id, task_name)

    def topological_sort(self):
        return self.dag_parser.global_topological_sort()

    def global_topological_sort(self):
        return self.dag_parser.global_topological_sort()

    def party_topological_sort(self, role, party_id):
        return self.dag_parser.party_topological_sort(role, party_id)

    def infer_dependent_tasks(self, input_artifacts):
        return self.dag_parser.infer_dependent_tasks(input_artifacts)

    @property
    def task_parser(self):
        return TaskParser

    def component_ref_list(self, role, party_id):
        _list = []
        for name in self.party_topological_sort(role=role, party_id=party_id):
            node = self.get_task_node(role=role, party_id=party_id, task_name=name)
            if node:
                _list.append(node.component_ref)
        return _list

    def dataset_list(self, role, party_id):
        data_set = []
        for task_name in self.party_topological_sort(role=role, party_id=party_id):
            task_node = self.get_task_node(role=role, party_id=party_id, task_name=task_name)
            parties = self.get_task_runtime_parties(task_name=task_name)
            if task_node.component_ref.lower() == "reader" and job_utils.check_party_in(role, party_id, parties):
                name = task_node.runtime_parameters.get("name")
                namespace = task_node.runtime_parameters.get("namespace")
                data_set.append(DataSet(**{"name": name, "namespace": namespace}))
        return data_set

    def role_parameters(self, role, party_id):
        _dict = {}
        for task_name in self.party_topological_sort(role=role, party_id=party_id):
            task_node = self.get_task_node(task_name=task_name, role=role, party_id=party_id)
            _dict[task_node.component_ref] = task_node.runtime_parameters
        return _dict

    def get_runtime_roles_on_party(self, task_name, party_id):
        return self.dag_parser.get_runtime_roles_on_party(task_name, party_id)

    def get_task_runtime_parties(self, task_name):
        try:
            return self.dag_parser.get_task_runtime_parties(task_name)
        except:
            return []

    def get_component_ref(self, task_name):
        return self.dag_parser.get_component_ref(task_name)


class Party(BaseModel):
    role: str
    party_id: Union[str, int]
