from pydantic import BaseModel
from typing import Dict, Optional, Union, Any, List


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
    taskid: Optional[str]
    component: Optional[str]
    role: Optional[str]
    stage: Optional[str]
    party_id: Optional[Union[str, int]]
    inputs: Optional[TaskRuntimeInputSpec]
    conf: RuntimeConfSpec