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
from typing import Literal, Union, List, Dict, Optional

import pydantic
from pydantic import typing


class MetricData(pydantic.BaseModel):
    class Group(pydantic.BaseModel):
        name: str
        index: Optional[int]
    name: str
    type: Optional[str]
    groups: List[Group]
    step_axis: Optional[str]
    data: Union[List, Dict]


class DirectoryDataPool(pydantic.BaseModel):
    class DirectoryDataPoolMetadata(pydantic.BaseModel):
        uri: str
        format: str = "csv"
        name_template: str = "{name}"  # `name` and `uuid` allowed in template

    type: Literal["directory"]
    metadata: DirectoryDataPoolMetadata


class CustomDataPool(pydantic.BaseModel):
    type: Literal["custom"]
    metadata: dict


class DirectoryModelPool(pydantic.BaseModel):
    class DirectoryDataPoolMetadata(pydantic.BaseModel):
        uri: str
        format: str = "json"
        name_template: str = "{name}"  # `name` and `uuid` allowed in template

    type: Literal["directory"]
    metadata: DirectoryDataPoolMetadata


class CustomModelPool(pydantic.BaseModel):
    type: Literal["custom"]
    metadata: dict


class DirectoryMetricPool(pydantic.BaseModel):
    class DirectoryDataPoolMetadata(pydantic.BaseModel):
        uri: str
        format: str = "json"
        name_template: str = "{name}"  # `name` and `uuid` allowed in template

    type: Literal["directory"]
    metadata: DirectoryDataPoolMetadata


class CustomMetricPool(pydantic.BaseModel):
    type: Literal["custom"]
    metadata: dict


class OutputPoolConf(pydantic.BaseModel):
    data: Union[DirectoryDataPool, CustomDataPool]
    model: Union[DirectoryModelPool, CustomModelPool]
    metric: Union[DirectoryMetricPool, CustomMetricPool]


class IOMeta(pydantic.BaseModel):
    class InputMeta(pydantic.BaseModel):
        data: typing.Dict[str, Union[List[Dict], Dict]]
        model: typing.Dict[str, Union[List[Dict], Dict]]

    class OutputMeta(pydantic.BaseModel):
        data: typing.Dict[str, Union[List[Dict], Dict]]
        model: typing.Dict[str, Union[List[Dict], Dict]]
        metric: typing.Dict[str, Union[List[Dict], Dict]]

    inputs: InputMeta
    outputs: OutputMeta


class ComponentOutputMeta(pydantic.BaseModel):
    class Status(pydantic.BaseModel):
        code: int
        exceptions: typing.Optional[str]
    status: Status
    io_meta: typing.Optional[IOMeta]
