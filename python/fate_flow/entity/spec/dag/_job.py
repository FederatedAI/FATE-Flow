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
from typing import Optional, Union, Literal, Dict, List, Any, Tuple

from pydantic import BaseModel

from fate_flow.entity.spec.dag._output import OutputArtifacts
from fate_flow.entity.spec.dag._party import PartySpec
from fate_flow.entity.spec.dag._artifact import RuntimeInputArtifacts


class TaskSpec(BaseModel):
    component_ref: str
    dependent_tasks: Optional[List[str]]
    parameters: Optional[Dict[Any, Any]]
    inputs: Optional[RuntimeInputArtifacts]
    outputs: Optional[OutputArtifacts]
    parties: Optional[List[PartySpec]]
    conf: Optional[Dict[Any, Any]]
    stage: Optional[Union[Literal["train", "predict", "default", "cross_validation"]]]


class PartyTaskRefSpec(BaseModel):
    parameters: Optional[Dict[Any, Any]]
    conf: Optional[Dict]


class PartyTaskSpec(BaseModel):
    parties: Optional[List[PartySpec]]
    tasks: Optional[Dict[str, PartyTaskRefSpec]] = {}
    conf: Optional[dict] = {}


class EngineRunSpec(BaseModel):
    name: str
    conf: Optional[Dict]


class TaskConfSpec(BaseModel):
    engine_run: Optional[Dict]
    provider: Optional[str]
    timeout: Optional[int]
    launcher_name: Optional[str] = "default"
    env_vars: Optional[Dict]


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
    cores: Optional[int]
    computing_partitions: Optional[int]
    sync_type: Optional[Union[Literal["poll", "callback"]]]
    auto_retries: Optional[int]
    model_id: Optional[str]
    model_version: Optional[Union[str, int]]
    model_warehouse: Optional[PipelineModel]
    task: Optional[TaskConfSpec]
    extra: Optional[Dict[Any, Any]]


class DAGSpec(BaseModel):
    parties: List[PartySpec]
    conf: Optional[JobConfSpec]
    stage: Optional[Union[Literal["train", "predict", "default", "cross_validation"]]]
    tasks: Dict[str, TaskSpec]
    party_tasks: Optional[Dict[str, PartyTaskSpec]]


class DAGSchema(BaseModel):
    dag: Union[DAGSpec, Any]
    schema_version: str
    kind: str = "fate"
