from .api import APIClient
from .models.federated import FederatedAPI
from .models.scheduler import SchedulerAPI
from .models.worker import WorkerAPI


class FlowSchedulerClient:
    """
    A client for communicating with a flow server.
    """
    def __init__(self, host=None, port=None, protocol="http", api_version=None, timeout=None, remote_host=None,
                 remote_port=None, remote_protocol=None, federated_mode="SINGLE"):
        self.client = APIClient(host, port, protocol, api_version, timeout, remote_host, remote_port, remote_protocol, federated_mode)

    @property
    def federated(self):
        return FederatedAPI(client=self.client)

    @property
    def scheduler(self):
        return SchedulerAPI(client=self.client)

    @property
    def worker(self):
        return WorkerAPI(client=self.client)
