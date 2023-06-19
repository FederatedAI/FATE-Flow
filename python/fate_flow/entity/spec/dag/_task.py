from typing import Optional, Union, Dict, Any, List

import pydantic

from fate_flow.entity.spec.dag._artifact import ArtifactInputApplySpec, ArtifactOutputApplySpec
from fate_flow.entity.spec.dag._computing import StandaloneComputingSpec, SparkComputingSpec, EggrollComputingSpec
from fate_flow.entity.spec.dag._device import CPUSpec, GPUSpec
from fate_flow.entity.spec.dag._federation import StandaloneFederationSpec, RollSiteFederationSpec, RabbitMQFederationSpec,PulsarFederationSpec,OSXFederationSpec
from fate_flow.entity.spec.dag._logger import FlowLogger
from fate_flow.entity.spec.dag._mlmd import MLMDSpec


class PreTaskConfigSpec(pydantic.BaseModel):
    class TaskConfSpec(pydantic.BaseModel):
        device: Union[CPUSpec, GPUSpec]
        computing: Union[StandaloneComputingSpec, EggrollComputingSpec, SparkComputingSpec]
        federation: Union[
            StandaloneFederationSpec,
            RollSiteFederationSpec,
            RabbitMQFederationSpec,
            PulsarFederationSpec,
            OSXFederationSpec,
        ]
        logger: Union[FlowLogger]

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
    input_artifacts: Dict[str, Union[List[ArtifactInputApplySpec], ArtifactInputApplySpec]] = {}
    conf: TaskConfSpec
    mlmd: MLMDSpec


class TaskConfigSpec(pydantic.BaseModel):
    class TaskConfSpec(pydantic.BaseModel):
        device: Union[CPUSpec, GPUSpec]
        computing: Union[StandaloneComputingSpec, EggrollComputingSpec, SparkComputingSpec]
        federation: Union[
            StandaloneFederationSpec,
            RollSiteFederationSpec,
            RabbitMQFederationSpec,
            PulsarFederationSpec,
            OSXFederationSpec,
        ]
        logger: Union[FlowLogger]

    job_id: Optional[str] = ""
    task_id: str
    party_task_id: str
    component: str
    role: str
    party_id: str
    stage: str = "default"
    parameters: Dict[str, Any] = {}
    input_artifacts: Dict[str, Union[List[ArtifactInputApplySpec], ArtifactInputApplySpec]] = {}
    output_artifacts: Dict[str, ArtifactOutputApplySpec] = {}
    conf: TaskConfSpec
