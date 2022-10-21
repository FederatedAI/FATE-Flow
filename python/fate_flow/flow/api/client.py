import json
import time

import requests

from ..conf import DEFAULT_TIMEOUT_SECONDS, DEFAULT_API_VERSION, DEFAULT_HTTP_HOST, DEFAULT_HTTP_PORT, \
    REQUEST_TRY_TIMES, DEFAULT_PROTOCOL
from ..utils.grpc_utils import wrap_grpc_packet
from ..utils.request_utils import get_exponential_backoff_interval
from ..utils.grpc_utils import gen_routing_metadata, get_command_federation_channel


class APIClient(requests.Session):
    def __init__(self, base_url=None, api_version=None, timeout=DEFAULT_TIMEOUT_SECONDS):
        super().__init__()
        self.timeout = timeout
        self.base_url = base_url
        self.api_version = api_version

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

    @property
    def version(self):
        if self.api_version:
            return self.api_version
        if DEFAULT_API_VERSION:
            return DEFAULT_API_VERSION
        return None

    @classmethod
    def remote(cls, job_id, method, endpoint, src_party_id, dest_party_id, src_role, json_body, federated_mode, host,
               port, protocol):
        src_party_id = str(src_party_id or '')
        dest_party_id = str(dest_party_id or '')

        kwargs = {
            'job_id': job_id,
            'method': method,
            'endpoint': endpoint,
            'src_party_id': src_party_id,
            'dest_party_id': dest_party_id,
            'src_role': src_role,
            'json_body': json_body,

        }

        if federated_mode == "SINGLE" or kwargs['dest_party_id'] == '0':
            return cls.remote_on_http(**kwargs)

        if federated_mode == "MULTIPLE":
            kwargs.update({
                'host': host,
                'port': port,
            })

            if protocol == "http":
                return cls.remote_on_http(**kwargs)

            if protocol == "grpc":
                return cls.remote_on_grpc(**kwargs)

            raise Exception(f'{protocol} coordination communication protocol is not supported.')

        raise Exception(f'{federated_mode} work mode is not supported')

    @staticmethod
    def remote_on_http(job_id, method, host, port, endpoint, try_times=None, timeout=None, **kwargs):
        if not try_times:
            try_times = REQUEST_TRY_TIMES
        if not timeout:
            timeout = DEFAULT_TIMEOUT_SECONDS
        for t in range(try_times):
            try:
                response = requests.request(method=method, url=f"{DEFAULT_PROTOCOL}://{host}:{port}/{endpoint}",
                                            timeout=timeout, **kwargs)
                response.raise_for_status()
            except Exception as e:
                if t >= DEFAULT_TIMEOUT_SECONDS - 1:
                    raise e
            else:
                return response.json()
            time.sleep(get_exponential_backoff_interval(t))

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
