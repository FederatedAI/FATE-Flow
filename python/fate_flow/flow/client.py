from .api import APIClient
from .models.federated import FederatedAPI
from .models.scheduler import SchedulerAPI
from .models.worker import WorkerAPI


class FlowClient:
    """
    A client for communicating with a flow server.
    """
    def __init__(self, base_url=None, api_version=None, timeout=None):
        self.client = APIClient(base_url, api_version, timeout)

    @property
    def federated(self):
        return FederatedAPI(client=self.client)

    @property
    def scheduler(self):
        return SchedulerAPI(client=self.client)

    @property
    def worker(self):
        return WorkerAPI(client=self.client)
