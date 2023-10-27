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
import threading
import time
import uuid

import requests

from ...entity import BFIAHttpHeadersSpec

FEDERATED_ERROR = 104


class APIClient(requests.Session):
    def __init__(self, host="127.0.0.1", port=9380, protocol="http", api_version=None, timeout=60,
                 remote_protocol="http", remote_host=None, remote_port=None, grpc_channel="default",
                 provider="FATE", route_table=None, self_node_id=""):
        super().__init__()
        self.host = host
        self.port = port
        self.protocol = protocol
        self.timeout = timeout
        self.api_version = api_version
        self.remote_protocol = remote_protocol
        self.remote_host = remote_host
        self.remote_port = remote_port
        self.grpc_channel = grpc_channel
        self.provider = provider
        self.route_table = route_table
        self.node_id = self_node_id

    @property
    def base_url(self):
        return f'{self.protocol}://{self.host}:{self.port}'

    @property
    def version(self):
        if self.api_version:
            return self.api_version
        return None

    def post(self, endpoint, data=None, json=None, **kwargs):
        return self.request('POST', url=self._set_url(endpoint), data=data, json=json,
                            **self._set_request_timeout(kwargs))

    def send_file(self, endpoint, data=None, json=None, params=None, files=None, **kwargs):
        return self.request('POST', url=self._set_url(endpoint), data=data, json=json, files=files, params=params,
                            **self._set_request_timeout(kwargs))

    def get(self, endpoint, **kwargs):
        kwargs.setdefault('allow_redirects', True)
        return self.request('GET', url=self._set_url(endpoint), **self._set_request_timeout(kwargs))

    def put(self, endpoint, data=None, **kwargs):
        return self.request('PUT', url=self._set_url(endpoint), data=data, **self._set_request_timeout(kwargs))

    def delete(self, endpoint, **kwargs):
        return self.request('DELETE', url=self._set_url(endpoint), **self._set_request_timeout(kwargs))

    @property
    def url(self):
        return self._url

    @property
    def _url(self):
        if self.version:
            return f"{self.base_url}/{self.version}"
        else:
            return self.base_url

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

    def remote(
            self, method, endpoint, dest_node_id, body, is_local=False, extra_params=None,
            headers=None
    ):

        if not self.route_table:
            raise Exception(f'Route table is null')
        if not headers:
            headers = {}
        headers.update(
            BFIAHttpHeadersSpec(
                x_auth_sign="",
                x_node_id=self.node_id,
                x_nonce=str(uuid.uuid4()),
                x_trace_id="",
                x_timestamp=str(int(time.time() * 1000))
            ).dict()
        )
        kwargs = {
            'method': method,
            'endpoint': endpoint,
            'json_body': body,
            "headers": headers
        }

        if extra_params:
            kwargs.update(extra_params)

        if is_local:
            return self.remote_on_http(**kwargs)

        elif dest_node_id in self.route_table:
            kwargs.update({
                "host": self.route_table[dest_node_id]["host"],
                "port": self.route_table[dest_node_id]["port"],
            })
            return self.remote_on_http(**kwargs)

        else:
            raise Exception(f'No found node id {dest_node_id} in route table: {self.route_table}')

    def remote_on_http(self, method, endpoint, host=None, port=None, try_times=3, timeout=10, json_body=None,
                       headers=None, **kwargs):
        if host and port:
            url = f"http://{host}:{port}{endpoint}"
        else:
            url = f"{self.base_url}{endpoint}"
        for t in range(try_times):
            try:
                response = requests.request(method=method, url=url, timeout=timeout, json=json_body, headers=headers)
                response.raise_for_status()
            except Exception as e:
                if t >= try_times - 1:
                    raise e
            else:
                try:
                    return response.json()
                except:
                    raise Exception(response.text)


class BaseAPI:
    def __init__(self, client: APIClient, callback=None):
        self.client = client
        self.callback = callback

    def federated_command(
            self, dest_node_id, endpoint, body, federated_response, method='POST', only_scheduler=False,
            extra_params=None
    ):
        try:
            headers = {}
            response = self.client.remote(
                method=method,
                endpoint=endpoint,
                dest_node_id=dest_node_id,
                body=body if body else {},
                extra_params=extra_params,
                is_local=self.is_local(node_id=dest_node_id),
                headers=headers
            )
            if only_scheduler:
                return response
        except Exception as e:
            response = {
                "code": FEDERATED_ERROR,
                "message": "Federated schedule error, {}".format(e)
            }
        if only_scheduler:
            return response
        federated_response[dest_node_id] = response

    @staticmethod
    def is_local(node_id):
        return node_id == "0"

    def job_command(self, node_list, endpoint, command_body=None, parallel=False, method="POST"):
        federated_response = {}
        threads = []
        if not command_body:
            command_body = {}
        for node_id in node_list:
            federated_response[node_id] = {}
            kwargs = {
                "dest_node_id": node_id,
                "endpoint": endpoint,
                "body": command_body,
                "federated_response": federated_response,
                "method": method
            }
            if parallel:
                t = threading.Thread(target=self.federated_command, kwargs=kwargs)
                threads.append(t)
                t.start()
            else:
                self.federated_command(**kwargs)
        for thread in threads:
            thread.join()
        return federated_response


    def scheduler_command(self, endpoint, node_id, command_body=None, method='POST'):
        try:
            federated_response = {}
            response = self.federated_command(
                method=method,
                endpoint=endpoint,
                dest_node_id=node_id,
                body=command_body if command_body else {},
                federated_response=federated_response,
                only_scheduler=True,
            )
        except Exception as e:
            response = {
                "code": FEDERATED_ERROR,
                "message": "Federated schedule error, {}".format(e)
            }
        return response
