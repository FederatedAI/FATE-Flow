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
    parameters: Optional[Dict[str, str]]
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
    engine: str
    computing_id: str


class FederationPartySpec(BaseModel):
    local: Dict[str, str]
    parties: List[Dict[str, str]]


class FederationBackendSpec(BaseModel):
    engine: str
    federation_id: str
    parties: FederationPartySpec


class RuntimeConfSpec(BaseModel):
    mlmd: Optional[MLMDSpec]
    logger: Optional[LOGGERSpec]
    device: Optional[str]
    computing: Optional[ComputingBackendSpec]
    federation: Optional[FederationBackendSpec]


class TaskScheduleSpec(BaseModel):
    execution_id: Optional[str]
    component: Optional[str]
    role: Optional[str]
    stage: Optional[str]
    party_id: Optional[Union[str, int]]
    inputs: Optional[TaskRuntimeInputSpec]
    outputs: Optional[Dict[str, IOArtifact]]
    conf: Optional[RuntimeConfSpec]