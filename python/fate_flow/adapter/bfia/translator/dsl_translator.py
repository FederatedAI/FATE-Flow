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
import copy
from typing import Dict

from .component_spec import BFIAComponentSpec

from fate_flow.entity.spec.dag import (
    DAGSchema,
    DAGSpec,
    PartySpec,
    RuntimeTaskOutputChannelSpec,
    DataWarehouseChannelSpec,
    PartyTaskSpec,
    PartyTaskRefSpec,
    TaskSpec,
    RuntimeInputArtifacts,
    JobConfSpec,
    SourceInputArtifacts,
    OutputArtifactSpec,
    OutputArtifacts
)

from ..utils.spec.job import (
    BFIADagSpec,
    DagSchemaSpec,
    ConfSpec,
    InitiatorSpec,
    RoleSpec,
    JobCommonSpec,
    JobParamsSpec,
    TaskParamsSpec,
    DagComponentSpec,
    DataSpec,
    DagSpec
)


class Translator(object):
    @classmethod
    def translate_dag_to_bfia_dag(cls, dag_schema: DAGSchema, component_specs: Dict[str, BFIAComponentSpec]):
        bfia_dag = BFIADagSpec(
            flow_id=dag_schema.dag.flow_id,
            old_job_id=dag_schema.dag.old_job_id,
            config=cls.translate_dag_to_bfia_config(dag_schema.dag, dag_schema.schema_version),
            dag=cls.translate_dag_to_bfia_tasks(dag_schema.dag, component_specs, dag_schema.schema_version)
        )

        return DagSchemaSpec(
            kind=dag_schema.kind,
            schema_version=dag_schema.schema_version,
            dag=bfia_dag
        )

    @classmethod
    def translate_bfia_dag_to_dag(cls, bfia_dag_schema: DagSchemaSpec, component_specs: Dict[str, BFIAComponentSpec]):
        translated_dag_buf = dict()
        translated_dag_buf["schema_version"] = bfia_dag_schema.schema_version

        bfia_dag: BFIADagSpec = bfia_dag_schema.dag
        translated_dag_buf["schema_version"] = bfia_dag_schema.schema_version
        translated_dag_buf["kind"] = bfia_dag_schema.kind

        dag_spec_buf = dict()
        dag_spec_buf["initiator"] = (bfia_dag.config.initiator.role, bfia_dag.config.initiator.node_id)
        dag_spec_buf["parties"] = cls.get_party_spec_from_bfia_dag(bfia_dag)
        dag_spec_buf["flow_id"] = bfia_dag.flow_id
        dag_spec_buf["old_job_id"] = bfia_dag.old_job_id
        dag_spec_buf["conf"] = cls.translate_job_params_to_dag(bfia_dag)
        dag_spec_buf["tasks"] = cls.translate_bfia_tasks_to_dag(bfia_dag, component_specs)
        dag_spec_buf["party_tasks"] = cls.translate_party_tasks_to_dag(bfia_dag, component_specs, dag_spec_buf["tasks"])

        translated_dag_buf["dag"] = dag_spec_buf
        return DAGSchema(**translated_dag_buf)

    @classmethod
    def translate_job_params_to_dag(cls, bfia_dag: BFIADagSpec):
        job_conf = JobConfSpec(**bfia_dag.config.job_params.common.dict(exclude_defaults=True))
        return job_conf

    @classmethod
    def get_party_spec_from_bfia_dag(cls, bfia_dag: BFIADagSpec):
        parties = []

        for role, party_id_list in iter(bfia_dag.config.role):
            if not party_id_list:
                continue

            parties.append(PartySpec(role=role, party_id=party_id_list))

        return parties

    @classmethod
    def translate_bfia_tasks_to_dag(cls, bfia_dag: BFIADagSpec, component_specs: Dict[str, BFIAComponentSpec]):
        tasks = dict()

        common_params = bfia_dag.config.task_params.common
        for bfia_task in bfia_dag.dag.components:
            task_spec = TaskSpec(component_ref=bfia_task.componentName)
            task_name = bfia_task.name
            tasks[task_name] = task_spec

            if common_params and task_name in common_params:
                task_spec.parameters = common_params[task_name]

            dependencies = set()
            for input_desc in bfia_task.input:
                dependencies.add(input_desc.key.split(".", -1)[0])
            task_spec.dependent_tasks = list(dependencies)

            conf = dict()
            conf["provider"] = bfia_task.provider
            conf["version"] = bfia_task.version

            component_spec = component_specs[bfia_task.componentName]
            support_roles = set(component_spec.roleList)
            parties = []
            all_parties = cls.get_party_spec_from_bfia_dag(bfia_dag)

            for party in all_parties:
                if party.role in support_roles:
                    parties.append(party)

            task_spec.parties = parties

            if bfia_task.input:
                input_keys = dict()
                for input_dict in component_spec.inputData:
                    input_type = cls.get_source_type(input_dict["category"])
                    input_name = input_dict["name"]
                    if input_type not in input_keys:
                        input_keys[input_type] = []

                    input_keys[input_type].append(input_name)

                inputs = dict()
                for input_desc in bfia_task.input:
                    input_type = cls.get_source_type(input_desc.type)

                    if input_type not in inputs:
                        inputs[input_type] = dict()

                    producer_task, output_artifact_key = input_desc.key.split(".", -1)

                    input_spec = RuntimeTaskOutputChannelSpec(producer_task=producer_task,
                                                              output_artifact_key=output_artifact_key,
                                                              output_artifact_type_alias=input_desc.type)
                    input_name = input_keys[input_type].pop(0)

                    # TODO: bifa does not support multiple inputs yet
                    inputs[input_type][input_name] = dict(task_output_artifact=input_spec)

                task_spec.inputs = RuntimeInputArtifacts(**inputs)

            if bfia_task.output:
                output_keys = dict()
                for output_dict in component_spec.outputData:
                    output_name = output_dict["name"]
                    output_type = cls.get_source_type(output_dict["category"])

                    if output_type not in output_keys:
                        output_keys[output_type] = []

                    output_keys[output_type].append(output_name)

                outputs = dict()
                for output_dict in bfia_task.output:
                    output_alias = output_dict.key
                    output_type_alias = output_dict.type

                    output_type = cls.get_source_type(output_type_alias)
                    if output_type not in outputs:
                        outputs[output_type] = dict()

                    output_name = output_keys[output_type].pop(0)

                    outputs[output_type][output_name] = OutputArtifactSpec(
                        output_artifact_key_alias=output_alias,
                        output_artifact_type_alias=output_type_alias
                    )

                task_spec.outputs = OutputArtifacts(**outputs)

            task_spec.conf = conf
            tasks[task_name] = task_spec

        return tasks

    @classmethod
    def translate_party_tasks_to_dag(cls,
                                     bfia_dag: BFIADagSpec,
                                     component_specs: Dict[str, BFIAComponentSpec],
                                     tasks: Dict[str, TaskSpec]
                                     ):
        party_tasks = dict()
        if bfia_dag.config and bfia_dag.config.job_params:
            for role, role_config in iter(bfia_dag.config.job_params):
                if role == "common" or not role_config:
                    continue

                role_task_params = getattr(getattr(bfia_dag.config, "task_params", {}), role, {})

                for party_str, party_config in role_config.items():
                    party_id_indexes = list(map(int, party_str.split("|", -1)))
                    party_id_list = [getattr(bfia_dag.config.role, role)[party_id] for party_id in party_id_indexes]
                    party_task = PartyTaskSpec()
                    party_task.parties = [PartySpec(role=role, party_id=party_id_list)]
                    party_task.conf = party_config

                    if role_task_params and party_str in role_task_params:
                        party_task_params = role_task_params[party_str]
                        party_task.tasks = cls.get_party_task_params(party_task_params, component_specs, tasks)

                    site_name = "_".join(map(str, [role] + party_id_list))
                    party_tasks[site_name] = party_task

        if bfia_dag.config and bfia_dag.config.task_params:
            for role, role_params in iter(bfia_dag.config.task_params):
                if role == "common" or not role_params:
                    continue

                for party_str, party_task_params in role_params.items():
                    party_id_indexes = list(map(int, party_str.split("|", -1)))
                    party_id_list = [getattr(bfia_dag.config.role, role)[party_id] for party_id in party_id_indexes]
                    site_name = "_".join(map(str, [role] + party_id_list))

                    if site_name in party_tasks:
                        continue

                    party_task = PartyTaskSpec()
                    party_task.parties = [PartySpec(role=role, party_id=party_id_list)]
                    party_task.tasks = cls.get_party_task_params(party_task_params, component_specs, tasks)

                    party_tasks[site_name] = party_task

        return party_tasks

    @classmethod
    def get_party_task_params(cls,
                              party_task_params,
                              component_specs: Dict[str, BFIAComponentSpec],
                              tasks: Dict[str, TaskSpec]):
        party_task_specs = dict()

        for task_name, params in party_task_params.items():
            task_spec = PartyTaskRefSpec()
            params = copy.deepcopy(params)
            if "name" in params and "namespace" in params:
                """
                bfia support only single input yet
                """
                name = params.pop("name")
                namespace = params.pop("namespace")
                component_ref = tasks[task_name].component_ref
                input_name = component_specs[component_ref].inputData[0]["name"]

                task_spec.inputs = SourceInputArtifacts(
                    data={
                        input_name:
                            {
                                "data_warehouse": DataWarehouseChannelSpec(namespace=namespace, name=name)
                            }
                    }
                )

                party_task_specs[task_name] = task_spec

            if params:
                task_spec.parameters = params

        return party_task_specs

    @classmethod
    def translate_dag_to_bfia_config(cls, dag: DAGSpec, schema_version: str):
        bfia_conf_buf = dict(version=schema_version)

        if dag.initiator:
            bfia_conf_buf["initiator"] = InitiatorSpec(role=dag.initiator[0], node_id=dag.initiator[1])

        role_spec = RoleSpec()
        for party_spec in dag.parties:
            role = party_spec.role
            party_id_list = party_spec.party_id
            setattr(role_spec, role, party_id_list)

        bfia_conf_buf["role"] = role_spec

        job_params = JobParamsSpec()
        job_params.common = JobCommonSpec(**dag.conf.dict(exclude_defaults=True))

        if dag.party_tasks:
            parties_conf = dict()
            for site_name, party_task in dag.party_tasks.items():
                if party_task.conf:
                    role = party_task.parties[0].role
                    party_id_list = party_task.parties[0].party_id
                    party_id_indexes = [getattr(role_spec, role).index(party_id) for party_id in party_id_list]
                    party_str = "|".join(map(str, party_id_indexes))

                    if role not in parties_conf:
                        parties_conf[role] = dict()

                    parties_conf[role][party_str] = party_task.conf

            for role, conf in parties_conf.items():
                setattr(job_params, role, conf)

        bfia_conf_buf["job_params"] = job_params

        task_params = TaskParamsSpec()
        if dag.tasks:
            common_params = dict()
            for task_name, task_spec in dag.tasks.items():
                if task_spec.parameters:
                    common_params[task_name] = task_spec.parameters

            if common_params:
                task_params.common = common_params

        if dag.party_tasks:
            party_task_params = dict()
            for site_name, party_task in dag.party_tasks.items():
                if not party_task.tasks:
                    continue

                party_conf = dict()
                role = party_task.parties[0].role
                party_id_list = party_task.parties[0].party_id
                party_id_indexes = [getattr(role_spec, role).index(party_id) for party_id in party_id_list]
                party_str = "|".join(map(str, party_id_indexes))

                for task_name, party_task_spec in party_task.tasks.items():
                    party_conf[task_name] = dict()
                    if party_task_spec.parameters:
                        party_conf[task_name].update(party_task_spec.parameters)

                    if party_task_spec.inputs and party_task_spec.inputs.data:
                        data_warehouse = list(party_task_spec.inputs.data.values())[0]["data_warehouse"]
                        party_conf[task_name]["name"] = data_warehouse.name
                        party_conf[task_name]["namespace"] = data_warehouse.namespace

                if role not in party_task_params:
                    party_task_params[role] = dict()
                party_task_params[role][party_str] = party_conf

            for role, conf in party_task_params.items():
                setattr(task_params, role, conf)

        bfia_conf_buf["task_params"] = task_params

        return ConfSpec(**bfia_conf_buf)

    @classmethod
    def translate_dag_to_bfia_tasks(cls, dag: DAGSpec, component_specs: Dict[str, BFIAComponentSpec], schema_version):
        bfia_dag_buf = dict(version=schema_version)

        tasks = []
        if dag.tasks:
            for task_name, task_spec in dag.tasks.items():
                bfia_task_spec = DagComponentSpec(
                    provider=task_spec.conf["provider"],
                    version=task_spec.conf["version"],
                    name=task_name,
                    componentName=task_spec.component_ref
                )

                component_spec = component_specs[task_spec.component_ref]
                inputs = []
                if task_spec.inputs:
                    for input_desc in component_spec.inputData:
                        input_type = cls.get_source_type(input_desc["category"])
                        input_key = input_desc["name"]

                        input_artifact_specs = getattr(task_spec.inputs, input_type, {})
                        if not input_artifact_specs or input_key not in input_artifact_specs:
                            continue

                        input_spec = input_artifact_specs[input_key]

                        producer_task = input_spec["task_output_artifact"].producer_task
                        output_artifact_key = input_spec["task_output_artifact"].output_artifact_key
                        type_alias = input_spec["task_output_artifact"].output_artifact_type_alias

                        inputs.append(DataSpec(type=type_alias, key=".".join([producer_task, output_artifact_key])))

                bfia_task_spec.input = inputs

                outputs = []
                if task_spec.outputs:
                    for output_desc in component_spec.outputData:
                        output_type = cls.get_source_type(output_desc["category"])
                        output_key = output_desc["name"]

                        output_artifacts = getattr(task_spec.outputs, output_type, {})
                        if not output_artifacts or output_key not in output_artifacts:
                            continue

                        output_spec: OutputArtifactSpec = output_artifacts[output_key]

                        if not output_spec:
                            continue

                        outputs.append(DataSpec(type=output_spec.output_artifact_type_alias,
                                                key=output_spec.output_artifact_key_alias))

                bfia_task_spec.output = outputs

                tasks.append(bfia_task_spec)

        if tasks:
            bfia_dag_buf["components"] = tasks

        return DagSpec(**bfia_dag_buf)

    @classmethod
    def get_source_type(cls, type_keyword):
        if "dataset" in type_keyword:
            return "data"
        elif "model" in type_keyword:
            return "model"
        else:
            return "metric"
