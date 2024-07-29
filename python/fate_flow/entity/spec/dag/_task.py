from typing import Optional, Union, Dict, Any, List

import pydantic

from fate_flow.entity.spec.dag._artifact import ArtifactInputApplySpec, ArtifactOutputApplySpec, \
    FlowRuntimeInputArtifacts
from fate_flow.entity.spec.dag._computing import StandaloneComputingSpec, SparkComputingSpec, EggrollComputingSpec
from fate_flow.entity.spec.dag._device import CPUSpec, GPUSpec
from fate_flow.entity.spec.dag._federation import StandaloneFederationSpec, RollSiteFederationSpec, RabbitMQFederationSpec,PulsarFederationSpec,OSXFederationSpec
from fate_flow.entity.spec.dag._logger import FlowLogger
from fate_flow.entity.spec.dag._mlmd import MLMDSpec


class TaskRuntimeConfSpec(pydantic.BaseModel):
    device: Union[CPUSpec, GPUSpec]
    computing: Union[StandaloneComputingSpec, EggrollComputingSpec, SparkComputingSpec]
    storage: Optional[str]
    federation: Union[
        StandaloneFederationSpec,
        RollSiteFederationSpec,
        RabbitMQFederationSpec,
        PulsarFederationSpec,
        OSXFederationSpec,
    ]
    logger: Union[FlowLogger]


class PreTaskConfigSpec(pydantic.BaseModel):
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
    parameters: Dict[str, Any] = {}
    input_artifacts: FlowRuntimeInputArtifacts = {}
    conf: TaskRuntimeConfSpec
    mlmd: MLMDSpec
    engine_run: Optional[Dict[str, Any]] = {}
    computing_partitions: int = None
    launcher_name: Optional[str] = "default"
    launcher_conf: Optional[Dict] = {}
    env_vars: Optional[Dict] = {}


class TaskConfigSpec(pydantic.BaseModel):
    job_id: Optional[str] = ""
    task_id: str
    party_task_id: str
    task_name: str
    component: str
    role: str
    party_id: str
    stage: str = "default"
    parameters: Dict[str, Any] = {}
    input_artifacts: Optional[Dict[str, Union[List[ArtifactInputApplySpec], ArtifactInputApplySpec, None]]] = {}
    output_artifacts: Optional[Dict[str, Union[ArtifactOutputApplySpec, None]]] = {}
    conf: TaskRuntimeConfSpec


class TaskCleanupConfigSpec(pydantic.BaseModel):
    computing: Union[StandaloneComputingSpec, EggrollComputingSpec, SparkComputingSpec]
    federation: Union[
        StandaloneFederationSpec,
        RollSiteFederationSpec,
        RabbitMQFederationSpec,
        PulsarFederationSpec,
        OSXFederationSpec,
    ]
