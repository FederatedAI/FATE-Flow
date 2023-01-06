from .models.resource import APIClient
from .models.federated import Federated
from .models.scheduler import Scheduler
from .models.worker import Worker


class FlowSchedulerApi:
    """
    A client for communicating with a flow server.
    """
    def __init__(self, host="127.0.0.1", port=9380, protocol="http", api_version=None, timeout=60,
                 remote_protocol="http", remote_host=None, remote_port=None, grpc_channel="default"):
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
        self.federated = Federated(client=self.client)
        self.scheduler = Scheduler(client=self.client)
        self.worker = Worker(client=self.client)
