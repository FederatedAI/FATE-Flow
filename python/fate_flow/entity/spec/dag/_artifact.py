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

import re
from typing import Optional, List, Literal, TypeVar, Dict, Union

import pydantic

# see https://www.rfc-editor.org/rfc/rfc3986#appendix-B
# scheme    = $2
# authority = $4
# path      = $5
# query     = $7
# fragment  = $9
from ._party import PartySpec

_uri_regex = re.compile(r"^(([^:/?#]+):)?(//([^/?#]*))?([^?#]*)(\?([^#]*))?(#(.*))?")


class ArtifactSource(pydantic.BaseModel):
    task_id: str
    party_task_id: str
    task_name: str
    component: str
    output_artifact_key: str
    output_index: Optional[int] = None


class Metadata(pydantic.BaseModel):
    class DataOverview(pydantic.BaseModel):
        count: Optional[int] = None
        samples: Optional[List] = None
    metadata: dict = pydantic.Field(default_factory=dict)
    name: Optional[str] = None
    namespace: Optional[str] = None
    model_overview: Optional[dict] = {}
    data_overview: Optional[DataOverview]
    source: Optional[ArtifactSource] = None
    model_key: Optional[str]
    type_name: Optional[str]
    index: Optional[Union[int, None]] = None

    class Config:
        extra = "forbid"


class ArtifactInputApplySpec(pydantic.BaseModel):
    uri: str
    metadata: Metadata
    type_name: Optional[str] = None

    def get_uri(self) -> "URI":
        return URI.from_string(self.uri)


class ArtifactOutputApplySpec(pydantic.BaseModel):
    uri: str
    _is_template: Optional[bool] = None
    type_name: Optional[str] = None

    def get_uri(self, index) -> "URI":
        if self.is_template():
            return URI.from_string(self.uri.format(index=index))
        else:
            if index != 0:
                raise ValueError(f"index should be 0, but got {index}")
            return URI.from_string(self.uri)

    def is_template(self) -> bool:
        return "{index}" in self.uri

    def _check_is_template(self) -> bool:
        return "{index}" in self.uri

    @pydantic.validator("uri")
    def _check_uri(cls, v, values) -> str:
        if not _uri_regex.match(v):
            raise pydantic.ValidationError(f"`{v}` is not valid uri")
        return v


class ArtifactOutputSpec(pydantic.BaseModel):
    uri: str
    metadata: Metadata
    type_name: str
    consumed: Optional[bool] = None


class URI:
    def __init__(
        self,
        schema: str,
        path: str,
        query: Optional[str] = None,
        fragment: Optional[str] = None,
        authority: Optional[str] = None,
    ):
        self.schema = schema
        self.path = path
        self.query = query
        self.fragment = fragment
        self.authority = authority

    @classmethod
    def from_string(cls, uri: str) -> "URI":
        match = _uri_regex.fullmatch(uri)
        if match is None:
            raise ValueError(f"`{uri}` is not valid uri")
        _, schema, _, authority, path, _, query, _, fragment = match.groups()
        return URI(schema=schema, path=path, query=query, fragment=fragment, authority=authority)

    @classmethod
    def load_uri(cls, engine, address):
        pass


class RuntimeTaskOutputChannelSpec(pydantic.BaseModel):
    producer_task: str
    output_artifact_key: str
    output_artifact_type_alias: Optional[str]
    parties: Optional[List[PartySpec]]

    class Config:
        extra = "forbid"


class DataWarehouseChannelSpec(pydantic.BaseModel):
    job_id: Optional[str]
    producer_task: Optional[str]
    output_artifact_key: Optional[str]
    namespace: Optional[str]
    name: Optional[str]
    dataset_id: Optional[str]
    parties: Optional[List[PartySpec]]

    class Config:
        extra = "forbid"


class ModelWarehouseChannelSpec(pydantic.BaseModel):
    model_id: Optional[str]
    model_version: Optional[str]
    producer_task: str
    output_artifact_key: str
    parties: Optional[List[PartySpec]]

    class Config:
        extra = "forbid"


InputArtifactSpec = TypeVar("InputArtifactSpec",
                            RuntimeTaskOutputChannelSpec,
                            ModelWarehouseChannelSpec,
                            DataWarehouseChannelSpec)


class RuntimeInputArtifacts(pydantic.BaseModel):
    data: Optional[Dict[str, Dict[str, Union[List[InputArtifactSpec], InputArtifactSpec]]]]
    model: Optional[Dict[str, Dict[str, Union[List[InputArtifactSpec], InputArtifactSpec]]]]


class FlowRuntimeInputArtifacts(pydantic.BaseModel):
    data: Optional[Dict[str, Union[InputArtifactSpec, List[InputArtifactSpec]]]]
    model: Optional[Dict[str, Union[InputArtifactSpec, List[InputArtifactSpec]]]]
