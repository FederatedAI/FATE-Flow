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
from typing import Any, List, Union, Literal, Dict

from pydantic import BaseModel


class PartySpec(BaseModel):
    role: Union[Literal["guest", "host", "arbiter"]]
    party_id: List[Union[str, int]]


class SchedulerInfoSpec(BaseModel):
    dag: Dict[str, Any]
    parties: List[PartySpec]
    initiator_party_id: str
    scheduler_party_id: str
    federated_status_collect_type: str
    model_id: str
    model_version: Union[str, int]

