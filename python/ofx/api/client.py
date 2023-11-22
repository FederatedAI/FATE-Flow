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
from .entity import PROTOCOL


class BaseApi(object):
    @property
    def federated(self):
        return

    @property
    def scheduler(self):
        return

    @property
    def worker(self):
        return

    @staticmethod
    def get_name():
        return "base"


class FlowSchedulerApi(BaseApi):
    """
    A client for communicating with a flow server.
    """
    def __init__(self, host="127.0.0.1", port=9380, protocol="http", api_version=None, timeout=60,
                 remote_protocol="http", remote_host=None, remote_port=None, grpc_channel="default",
                 callback=None):
        from .models.fate_flow.resource import APIClient
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
        self.callback = callback

    @property
    def federated(self):
        from .models.fate_flow.federated import Federated
        return Federated(client=self.client, callback=self.callback)

    @property
    def scheduler(self):
        from .models.fate_flow.scheduler import Scheduler
        return Scheduler(client=self.client, callback=self.callback)

    @property
    def worker(self):
        from .models.fate_flow.worker import Worker
        return Worker(client=self.client, callback=self.callback)

    @staticmethod
    def get_name():
        return PROTOCOL.FATE_FLOW


class BfiaSchedulerApi(BaseApi):
    """
    A client for communicating with a interconnect server.
    """
    def __init__(self, host="127.0.0.1", port=9380, protocol="http", api_version=None, timeout=60,
                 remote_protocol="http", remote_host=None, remote_port=None, grpc_channel="default",
                 callback=None, route_table=None, self_node_id=None):
        from .models.bfia.resource import APIClient
        self.client = APIClient(
            host=host,
            port=port,
            protocol=protocol,
            api_version=api_version,
            timeout=timeout,
            remote_host=remote_host,
            remote_port=remote_port,
            remote_protocol=remote_protocol,
            grpc_channel=grpc_channel,
            route_table=route_table,
            self_node_id=self_node_id
        )
        self.callback = callback

    @property
    def federated(self):
        from .models.bfia.federated import Federated
        return Federated(client=self.client, callback=self.callback)

    @property
    def scheduler(self):
        from .models.bfia.scheduler import Scheduler
        return Scheduler(client=self.client, callback=self.callback)

    @property
    def worker(self):
        from .models.bfia.worker import Worker
        return Worker(client=self.client, callback=self.callback)

    @staticmethod
    def get_name():
        return PROTOCOL.BFIA


class CommonSchedulerApi(BaseApi):
    """
    A client for communicating with a kuscia server.
    """
    def __init__(self, host="127.0.0.1", port=9380, protocol="http", api_version=None, timeout=60,
                 remote_protocol="http", remote_host=None, remote_port=None, grpc_channel="default",
                 client_cert=None, client_key=None,client_ca=None, veritfy=None, token=None, restful=False,
                 callback=None):
        from .models.common_module.resource import CommonApiClient
        self.client = CommonApiClient(
            remote_host=remote_host,
            remote_port=remote_port,
            client_cert=client_cert,
            client_key=client_key,
            client_ca=client_ca,
            veritfy=veritfy,
            token=token,
            restful=restful,

        )
        self.callback = callback

    @property
    def federated(self):
        from .models.common_module.federated import Federated
        return Federated(client=self.client, callback=self.callback)


def load_schedule_clients(**kwargs):
    clients = {}
    for obj in [FlowSchedulerApi]:
        name = obj.get_name()
        clients[name] = obj(**kwargs)
    return clients
