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
from typing import Optional, Dict, List, Union, Any, Literal
from pydantic import BaseModel


class ParameterSpec(BaseModel):
    type: str
    default: Optional[Any]
    optional: bool
    description: str = ""
    type_meta: dict = {}


class ArtifactSpec(BaseModel):
    types: List[str]
    optional: bool
    stages: Optional[List[str]]
    roles: Optional[List[str]]
    description: str = ""
    is_multi: bool


class InputArtifactsSpec(BaseModel):
    data: Dict[str, ArtifactSpec]
    model: Dict[str, ArtifactSpec]


class OutputArtifactsSpec(BaseModel):
    data: Dict[str, ArtifactSpec]
    model: Dict[str, ArtifactSpec]
    metric: Dict[str, ArtifactSpec]


class ComponentSpec(BaseModel):
    name: str
    description: str
    provider: str
    version: str
    labels: List[str] = ["trainable"]
    roles: List[str]
    parameters: Dict[str, ParameterSpec]
    input_artifacts: InputArtifactsSpec
    output_artifacts: OutputArtifactsSpec


class RuntimeOutputChannelSpec(BaseModel):
    producer_task: str
    output_artifact_key: str


class RuntimeInputDefinition(BaseModel):
    parameters: Optional[Dict[str, Any]]
    artifacts: Optional[Dict[str, Dict[str, RuntimeOutputChannelSpec]]]


class ArtifactTypeSpec(BaseModel):
    type_name: str
    uri_types: List[str]
    path_type: Literal["file", "directory", "distributed", "unresolved"]


class ComponentIOArtifactTypeSpec(BaseModel):
    name: str
    is_multi: bool
    optional: bool
    types: List[ArtifactTypeSpec]


class ComponentIOInputsArtifactsTypeSpec(BaseModel):
    data: List[ComponentIOArtifactTypeSpec]
    model: List[ComponentIOArtifactTypeSpec]


class ComponentIOOutputsArtifactsTypeSpec(BaseModel):
    data: List[ComponentIOArtifactTypeSpec]
    model: List[ComponentIOArtifactTypeSpec]
    metric: List[ComponentIOArtifactTypeSpec]


class ComponentIOArtifactsTypeSpec(BaseModel):
    inputs: ComponentIOInputsArtifactsTypeSpec
    outputs: ComponentIOOutputsArtifactsTypeSpec


class ComponentSpecV1(BaseModel):
    component: ComponentSpec
    schema_version: str = "v1"
