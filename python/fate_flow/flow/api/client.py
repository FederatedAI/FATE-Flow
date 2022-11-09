import json
import time

import requests

from ..conf import DEFAULT_TIMEOUT_SECONDS, DEFAULT_API_VERSION, DEFAULT_HTTP_HOST, DEFAULT_HTTP_PORT, \
    REQUEST_TRY_TIMES, DEFAULT_PROTOCOL
from ..utils.grpc_utils import wrap_grpc_packet
from ..utils.request_utils import get_exponential_backoff_interval
from ..utils.grpc_utils import gen_routing_metadata, get_command_federation_channel
from fate_flow.utils.log_utils import schedule_logger


class APIClient(requests.Session):
    def __init__(self, host=None, port=None, protocol="http", api_version=None, timeout=None, remote_host=None,
                 remote_port=None, remote_protocol=None, federated_mode="SINGLE"):
        super().__init__()

        self.host = host
        self.port = port
        self.protocol = protocol
        self._timeout = timeout
        self.api_version = api_version
        self.remote_host = remote_host
        self.remote_port = remote_port
        self.remote_protocol = remote_protocol
        self.federated_mode = federated_mode

    @property
    def base_url(self):
        if self.host and self.port and self.protocol:
            return f'{self.protocol}://{self.host}:{self.port}'
        else:
            return f'{DEFAULT_PROTOCOL}://{DEFAULT_HTTP_HOST}:{DEFAULT_HTTP_PORT}'

    @property
    def timeout(self):
        if self._timeout:
            return self._timeout
        else:
            return DEFAULT_TIMEOUT_SECONDS

    @property
    def version(self):
        if self.api_version:
            return self.api_version
        if DEFAULT_API_VERSION:
            return DEFAULT_API_VERSION
        return None

    def post(self, endpoint, data=None, json=None, **kwargs):
        return self.request('POST', url=self._set_url(endpoint), data=data, json=json,
                            **self._set_request_timeout(kwargs))

    def get(self, endpoint, **kwargs):
        kwargs.setdefault('allow_redirects', True)
        return self.request('GET', url=self._set_url(endpoint), **self._set_request_timeout(kwargs))

    def put(self, endpoint, data=None, **kwargs):
        return self.request('PUT', url=self._set_url(endpoint), data=data, **self._set_request_timeout(kwargs))

    def delete(self, endpoint, **kwargs):
        return self.request('DELETE', url=self._set_url(endpoint), **self._set_request_timeout(kwargs))

    @property
    def _url(self):
        base_url = self.base_url if self.base_url else f'{DEFAULT_PROTOCOL}://{DEFAULT_HTTP_HOST}:{DEFAULT_HTTP_PORT}'
        if self.version:
            return f"{base_url}/{self.version}"
        else:
            return base_url

    def generate_endpoint(self, endpoint):
        if self.version:
            return f"{endpoint}/{self.version}"
        else:
            return endpoint

    def _set_request_timeout(self, kwargs):
        kwargs.setdefault('timeout', self.timeout)
        return kwargs

    def _set_url(self, endpoint):
        return f"{self._url}/{endpoint}"

    def remote(self, job_id, method, endpoint, src_party_id, dest_party_id, src_role, json_body, federated_mode=None,
               local=False):
        if self.version:
            endpoint = f"/{self.version}{endpoint}"
        federated_mode = federated_mode if federated_mode else self.federated_mode
        kwargs = {
            'job_id': job_id,
            'method': method,
            'endpoint': endpoint,
            'src_party_id': src_party_id,
            'dest_party_id': dest_party_id,
            'src_role': src_role,
            'json_body': json_body,

        }
        if self.federated_mode == "SINGLE" or local:
            return self.remote_on_http(**kwargs)

        if federated_mode == "MULTIPLE":
            host = self.remote_host
            port = self.remote_port
            if src_party_id == dest_party_id:
                host = self.host
                port = self.port
            kwargs.update({
                'host': host,
                'port': port,
            })

            if self.remote_protocol == "http":
                return self.remote_on_http(**kwargs)

            if self.remote_protocol == "grpc":
                return self.remote_on_grpc(**kwargs)

            raise Exception(f'{self.remote_protocol} coordination communication protocol is not supported.')

        raise Exception(f'{federated_mode} work mode is not supported')

    def remote_on_http(self, job_id, method, endpoint, host=None, port=None, try_times=None, timeout=None,
                       json_body=None, **kwargs):
        if not try_times:
            try_times = REQUEST_TRY_TIMES
        if not timeout:
            timeout = DEFAULT_TIMEOUT_SECONDS

        if host and port:
            url = f"{DEFAULT_PROTOCOL}://{host}:{port}{endpoint}"
        else:
            url = f"{self.base_url}{endpoint}"
        for t in range(try_times):
            try:
                response = requests.request(method=method, url=url, timeout=timeout, json=json_body)
                response.raise_for_status()
            except Exception as e:
                # if t >= DEFAULT_TIMEOUT_SECONDS - 1:
                    raise e
            else:
                return response.json()
            # time.sleep(get_exponential_backoff_interval(t))

    @staticmethod
    def remote_on_grpc(job_id, method, host, port, endpoint, src_party_id, dest_party_id, json_body,
                       try_times=None, timeout=None, headers=None, **kwargs):
        if not try_times:
            try_times = REQUEST_TRY_TIMES
        if not timeout:
            timeout = DEFAULT_TIMEOUT_SECONDS
        _packet = wrap_grpc_packet(
            json_body=json_body, http_method=method, url=endpoint,
            src_party_id=src_party_id, dst_party_id=dest_party_id,
            job_id=job_id, headers=headers, overall_timeout=timeout,
        )
        _routing_metadata = gen_routing_metadata(
            src_party_id=src_party_id, dest_party_id=dest_party_id,
        )

        for t in range(try_times):
            channel, stub = get_command_federation_channel(host, port)

            try:
                _return, _call = stub.unaryCall.with_call(
                    _packet, metadata=_routing_metadata,
                    timeout=timeout / 1000 or None,
                )
            except Exception as e:
                if t >= REQUEST_TRY_TIMES - 1:
                    raise e
            else:
                return json.loads(_return.body.value)
            finally:
                channel.close()
