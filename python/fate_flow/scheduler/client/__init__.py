from fate_flow.flow.client import FlowSchedulerClient
from fate_flow.settings import HOST, HTTP_PORT


class SchedulerClient(object):
    api: FlowSchedulerClient = None

    @classmethod
    def init(cls):
        api_version = "v1"
        remote_host = "127.0.0.1"
        remote_port = 9380
        remote_protocol = "http"
        federated_mode = "SINGLE"
        cls.api = FlowSchedulerClient(host=HOST, port=HTTP_PORT, protocol="http", api_version=api_version,
                                      remote_host=remote_host, remote_port=remote_port,
                                      remote_protocol=remote_protocol, federated_mode=federated_mode)
