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
import logging.config
import os.path
from typing import Optional, Dict, List, Union, Any, Literal, TypeVar
from pydantic import BaseModel


# component
class ParameterSpec(BaseModel):
    type: str
    default: Any
    optional: bool


class ArtifactSpec(BaseModel):
    type: str
    optional: bool
    stages: Optional[List[str]]
    roles: Optional[List[str]]


class InputDefinitionsSpec(BaseModel):
    parameters: Dict[str, ParameterSpec]
    artifacts: Dict[str, ArtifactSpec]


class OutputDefinitionsSpec(BaseModel):
    artifacts: Dict[str, ArtifactSpec]


class ComponentSpec(BaseModel):
    name: str
    description: str
    provider: str
    version: str
    labels: List[str] = ["trainable"]
    roles: List[str]
    input_definitions: InputDefinitionsSpec
    output_definitions: OutputDefinitionsSpec


class RuntimeOutputChannelSpec(BaseModel):
    producer_task: str
    output_artifact_key: str


class RuntimeInputDefinition(BaseModel):
    parameters: Optional[Dict[str, Any]]
    artifacts: Optional[Dict[str, Dict[str, RuntimeOutputChannelSpec]]]


# dag
class PartySpec(BaseModel):
    role: Union[Literal["guest", "host", "arbiter", "local"]]
    party_id: List[str]


class RuntimeTaskOutputChannelSpec(BaseModel):
    producer_task: str
    output_artifact_key: str
    roles: Optional[List[Literal["guest", "host", "arbiter", "local"]]]


class ModelWarehouseChannelSpec(BaseModel):
    model_id: Optional[str]
    model_version: Optional[Union[str, int]]
    producer_task: str
    output_artifact_key: str
    roles: Optional[List[Literal["guest", "host", "arbiter", "local"]]]


InputChannelSpec = TypeVar("InputChannelSpec", RuntimeTaskOutputChannelSpec, ModelWarehouseChannelSpec)


class TaskRuntimeInputDefinition(BaseModel):
    parameters: Optional[Dict[str, Any]]
    artifacts: Optional[Dict[str, Dict[str, Union[InputChannelSpec, List[InputChannelSpec]]]]]


class TaskSpec(BaseModel):
    component_ref: str
    dependent_tasks: Optional[List[str]]
    inputs: Optional[TaskRuntimeInputDefinition]
    parties: Optional[List[PartySpec]]
    conf: Optional[Dict[Any, Any]]
    stage: Optional[Union[Literal["train", "predict", "default"]]]


class PartyTaskRefSpec(BaseModel):
    inputs: TaskRuntimeInputDefinition
    conf: Optional[Dict]


class PartyTaskSpec(BaseModel):
    parties: Optional[List[PartySpec]]
    tasks: Dict[str, PartyTaskRefSpec]
    conf: Optional[dict]


class TaskConfSpec(BaseModel):
    engine: Optional[Dict[str, Any]]
    provider: Optional[str]


class InheritConfSpec(BaseModel):
    job_id: str
    task_list: List[str]


class JobConfSpec(BaseModel):
    class PipelineModel(BaseModel):
        model_id: str
        model_version: Union[str, int]
    priority: Optional[int]
    scheduler_party_id: Optional[str]
    initiator_party_id: Optional[str]
    inheritance: Optional[InheritConfSpec]
    task_parallelism: Optional[int]
    task_cores: Optional[int]
    sync_type: Optional[Union[Literal["poll", "callback"]]]
    auto_retries: Optional[int]
    model_id: Optional[str]
    model_version: Optional[Union[str, int]]
    model_warehouse: Optional[PipelineModel]
    task: Optional[TaskConfSpec]


class DAGSpec(BaseModel):
    parties: List[PartySpec]
    conf: Optional[JobConfSpec]
    stage: Optional[Union[Literal["train", "predict", "default"]]]
    tasks: Dict[str, TaskSpec]
    party_tasks: Optional[Dict[str, PartyTaskSpec]]


class DAGSchema(BaseModel):
    dag: DAGSpec
    schema_version: str


# task
class MLMDSpec(BaseModel):
    class MLMDMetadata:
        host: Optional[str]
        port: Optional[int]
        protocol: Optional[str]
    type: str
    metadata: Dict[str, Any]


class ComputingBackendSpec(BaseModel):
    type: str
    metadata: Dict[str, Any]


class DirectoryDataPool(BaseModel):
    class DirectoryDataPoolMetadata(BaseModel):
        uri: str
        format: str = "csv"
        name_template: str = "{name}"  # `name` and `uuid` allowed in template

    type: Literal["directory"]
    metadata: DirectoryDataPoolMetadata


class CustomDataPool(BaseModel):
    type: Literal["custom"]
    metadata: dict


class DirectoryModelPool(BaseModel):
    class DirectoryDataPoolMetadata(BaseModel):
        uri: str
        format: str = "json"
        name_template: str = "{name}"  # `name` and `uuid` allowed in template

    type: Literal["directory"]
    metadata: DirectoryDataPoolMetadata


class DirectoryMetricPool(BaseModel):
    class DirectoryDataPoolMetadata(BaseModel):
        uri: str
        format: str = "json"
        name_template: str = "{name}"  # `name` and `uuid` allowed in template

    type: Literal["directory"]
    metadata: DirectoryDataPoolMetadata


class CustomModelPool(BaseModel):
    type: Literal["custom"]
    metadata: dict


class CustomMetricPool(BaseModel):
    type: Literal["custom"]
    metadata: dict


class TaskArtifactSpec(BaseModel):
    name: str
    uri: str
    metadata: Optional[dict] = None


class FlowLogger(BaseModel):
    class FlowLoggerMetadata(BaseModel):
        basepath: str
        level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

    type: Literal["flow"]
    metadata: FlowLoggerMetadata

    def install(self):
        os.makedirs(self.metadata.basepath, exist_ok=True)
        levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        formatters = {"brief": {"format": "'%(asctime)s %(levelname)-8s %(name)s:%(lineno)s %(message)s'"}}
        handlers = {}
        filters = {}

        def add_file_handler(
            name,
            filename,
            level,
            formater="brief",
            filters=[]
        ):
            handlers[name] = {
                "class": "logging.FileHandler",
                "level": level,
                "formatter": formater,
                "filters": filters,
                "filename": filename
            }

        # add root logger
        root_handlers = []
        root_base_path = os.path.join(self.metadata.basepath, "root")
        os.makedirs(root_base_path, exist_ok=True)
        for level in levels:
            handler_name = f"root_{level.lower()}"
            add_file_handler(
                name=handler_name,
                filename=os.path.join(root_base_path, level),
                level=level,
            )
            root_handlers.append(handler_name)

        # add component logger
        component_handlers = []
        component_base_path = os.path.join(self.metadata.basepath, "component")
        os.makedirs(component_base_path, exist_ok=True)
        filters["components"] = {"name": "fate_flow.components"}
        for level in levels:
            handler_name = f"component_{level.lower()}"
            add_file_handler(
                name=handler_name,
                filename=os.path.join(component_base_path, level),
                level=level,
            )
            component_handlers.append(handler_name)
        component_loggers = {
            "fate_flow.components": dict(
                handlers=component_handlers,
                filters=["components"],
                level=self.metadata.level,
            )
        }

        logging.config.dictConfig(
            dict(
                version=1,
                formatters=formatters,
                handlers=handlers,
                filters=filters,
                loggers=component_loggers,
                root=dict(handlers=root_handlers, level=self.metadata.level),
                disable_existing_loggers=False,
            )
        )


class TaskConfigSpec(BaseModel):
    class TaskInputsSpec(BaseModel):
        parameters: Dict[str, Any] = {}
        artifacts: Dict[str, Union[TaskArtifactSpec, List[TaskArtifactSpec], InputChannelSpec]] = {}

    class TaskConfSpec(BaseModel):
        mlmd: MLMDSpec
        device: Any
        computing: ComputingBackendSpec
        federation: Any
        logger: FlowLogger
    model_id: Optional[str] = ""
    model_version: Optional[str] = ""
    job_id: Optional[str] = ""
    task_id: str
    task_version: str
    task_name: str
    provider_name: str = "fate"
    party_task_id: str
    component: str
    role: str
    party_id: str
    stage: str = "default"
    inputs: TaskInputsSpec = TaskInputsSpec(parameters={}, artifacts={})
    conf: TaskConfSpec
