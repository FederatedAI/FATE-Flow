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
from fate_flow.scheduler.scheduler import SchedulerABC
from fate_flow.runtime.runtime_config import RuntimeConfig
from fate_flow.runtime.system_settings import HOST, HTTP_PORT, PROXY_PROTOCOL, API_VERSION, HTTP_REQUEST_TIMEOUT
from fate_flow.utils.api_utils import get_federated_proxy_address, generate_headers
from ofx.api.client import FlowSchedulerApi


def init_scheduler():
    remote_host, remote_port, remote_protocol, grpc_channel = get_federated_proxy_address()

    protocol = remote_protocol if remote_protocol else PROXY_PROTOCOL

    # schedule client
    RuntimeConfig.set_schedule_client(
        FlowSchedulerApi(
            host=HOST,
            port=HTTP_PORT,
            api_version=API_VERSION,
            timeout=HTTP_REQUEST_TIMEOUT,
            remote_protocol=protocol,
            remote_host=remote_host,
            remote_port=remote_port,
            grpc_channel=grpc_channel,
            callback=generate_headers)
    )

