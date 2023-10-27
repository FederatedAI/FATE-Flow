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
from typing import Optional, List

import pydantic
from pydantic import BaseModel

OSX_EXCHANGE = ""


class PROTOCOL:
    FATE_FLOW = "fate"
    BFIA = "bfia"

class RoleSpec(BaseModel):
    guest: Optional[List[str]]
    host: Optional[List[str]]
    arbiter: Optional[List[str]]
    local: Optional[List[str]]


class BFIAHttpHeadersSpec(pydantic.BaseModel):
    x_auth_sign: Optional[str]
    x_node_id: Optional[str]
    x_nonce: Optional[str]
    x_trace_id: Optional[str]
    x_timestamp: Optional[str]


class BFIAHeadersSpec(pydantic.BaseModel):
    x_ptp_version: Optional[str]
    x_ptp_provider_code: Optional[str]
    x_ptp_trace_id: Optional[str]
    x_ptp_token: Optional[str]
    x_ptp_uri: Optional[str]
    x_ptp_from_node_id: Optional[str]
    x_ptp_from_inst_id: Optional[str]
    x_ptp_target_node_id: Optional[str]
    x_ptp_target_inst_id: Optional[str]
    x_ptp_session_id: Optional[str]
    x_ptp_topic: Optional[str]
