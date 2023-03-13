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
from .models.resource import APIClient
from .models.federated import Federated
from .models.scheduler import Scheduler
from .models.worker import Worker


class FlowSchedulerApi:
    """
    A client for communicating with a flow server.
    """
    def __init__(self, host="127.0.0.1", port=9380, protocol="http", api_version=None, timeout=60,
                 remote_protocol="http", remote_host=None, remote_port=None, grpc_channel="default",
                 callback=None):
        self.client = APIClient(
            host=host,
            port=port,
            protocol=protocol,
            api_version=api_version,
            timeout=timeout,
            remote_host=remote_host,
            remote_port=remote_port,
            remote_protocol=remote_protocol,
            grpc_channel=grpc_channel
        )
        self.federated = Federated(client=self.client, callback=callback)
        self.scheduler = Scheduler(client=self.client, callback=callback)
        self.worker = Worker(client=self.client, callback=callback)
