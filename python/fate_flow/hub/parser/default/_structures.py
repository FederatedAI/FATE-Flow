from typing import Optional, Dict, List, Union, Any, Literal, TypeVar
from pydantic import BaseModel

# task
class IOArtifact(BaseModel):
    name: str
    uri: str
    metadata: Optional[dict]


class InputSpec(BaseModel):
    parameters: Optional[Dict[str, Any]]
    artifacts: Optional[IOArtifact]


class TaskRuntimeInputSpec(BaseModel):
    parameters: Optional[Dict[str, Any]]
    artifacts: Optional[Dict[str, IOArtifact]]


class TaskRuntimeOutputSpec(BaseModel):
    artifacts: Dict[str, IOArtifact]


class MLMDSpec(BaseModel):
    type: str
    metadata: Dict[str, Any]


class LOGGERSpec(BaseModel):
    type: str
    metadata: Dict[str, Any]


class ComputingBackendSpec(BaseModel):
    type: str
    metadata: Dict[str, Any]


class FederationBackendSpec(BaseModel):
    type: str
    metadata: Dict[str, Any]


class OutputModelSpec(BaseModel):
    type: str
    metadata: Dict[str, str]


class OutputMetricSpec(BaseModel):
    type: str
    metadata: Dict[str, str]


class OutputDataSpec(BaseModel):
    type: str
    metadata: Dict[str, str]


class OutputSpec(BaseModel):
    model: OutputModelSpec
    metric: OutputMetricSpec
    data: OutputDataSpec


class RuntimeConfSpec(BaseModel):
    output: OutputSpec
    mlmd: MLMDSpec
    logger: LOGGERSpec
    device: Dict[str, str]
    computing: ComputingBackendSpec
    federation: FederationBackendSpec


class TaskScheduleSpec(BaseModel):
    task_id: Optional[str]
    party_task_id: Optional[str]
    component: Optional[str]
    role: Optional[str]
    stage: Optional[str]
    party_id: Optional[Union[str, int]]
    inputs: Optional[TaskRuntimeInputSpec]
    conf: RuntimeConfSpec

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
    role: Union[Literal["guest", "host", "arbiter"]]
    party_id: List[Union[str, int]]


class RuntimeTaskOutputChannelSpec(BaseModel):
    producer_task: str
    output_artifact_key: str
    roles: Optional[List[Literal["guest", "host", "arbiter"]]]


class ModelWarehouseChannelSpec(BaseModel):
    model_id: Optional[str]
    model_version: Optional[Union[str, int]]
    producer_task: str
    output_artifact_key: str
    roles: Optional[List[Literal["guest", "host", "arbiter"]]]


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
    task_cores: int
    engine: Dict[str, Any]


class JobConfSpec(BaseModel):
    scheduler_party_id: Optional[Union[str, int]]
    initiator_party_id: Optional[Union[str, int]]
    inherit: Optional[Dict[str, Any]]
    task_parallelism: Optional[int]
    task_cores: Optional[int]
    federated_status_collect_type: Optional[str]
    auto_retries: Optional[int]
    model_id: Optional[str]
    model_version: Optional[Union[str, int]]
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
