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

import json
import requests

from ...utils.grpc_utils import wrap_proxy_grpc_packet
from ...utils.grpc_utils import gen_routing_metadata, get_proxy_channel

FEDERATED_ERROR = 104


class APIClient(requests.Session):
    def __init__(self, host="127.0.0.1", port=9380, protocol="http", api_version=None, timeout=60,
                 remote_protocol="http", remote_host=None, remote_port=None, grpc_channel="default",
                 provider: str = "FATE", route_table=None):
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

    def remote(self, job_id, method, endpoint, src_party_id, dest_party_id, src_role, json_body, is_local=False,
               extra_params=None, headers=None):
        if not headers:
            headers = {}
        if self.version:
            endpoint = f"/{self.version}{endpoint}"
        kwargs = {
            'job_id': job_id,
            'method': method,
            'endpoint': endpoint,
            'src_party_id': src_party_id,
            'dest_party_id': dest_party_id,
            'src_role': src_role,
            'json_body': json_body,
            "headers": headers
        }
        if extra_params:
            kwargs.update(extra_params)
        if not self.remote_host and not self.remote_port and self.remote_protocol == "grpc":
            raise Exception(
                f'{self.remote_protocol} coordination communication protocol need remote host and remote port.')
        kwargs.update({
            "source_host": self.host,
            "source_port": self.port,
        })
        if is_local:
            return self.remote_on_http(**kwargs)
        if self.remote_host and self.remote_port:
            kwargs.update({
                "host": self.remote_host,
                "port": self.remote_port,
            })
            if self.remote_protocol == "http":
                return self.remote_on_http(**kwargs)
            if self.remote_protocol == "grpc":
                return self.remote_on_grpc_proxy(**kwargs)
            else:
                raise Exception(f'{self.remote_protocol} coordination communication protocol is not supported.')
        else:
            return self.remote_on_http(**kwargs)

    def remote_on_http(self, method, endpoint, host=None, port=None, try_times=3, timeout=10,
                       json_body=None, dest_party_id=None, service_name="fateflow", headers=None, **kwargs):
        headers.update({
            "dest-party-id": dest_party_id,
            "service": service_name
        })
        if host and port:
            url = f"{self.remote_protocol}://{host}:{port}{endpoint}"
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

    @staticmethod
    def remote_on_grpc_proxy(job_id, method, host, port, endpoint, src_party_id, dest_party_id, json_body,
                             try_times=3, timeout=10, headers=None, source_host=None, source_port=None, **kwargs):
        _packet = wrap_proxy_grpc_packet(
            json_body=json_body, http_method=method, url=endpoint,
            src_party_id=src_party_id, dst_party_id=dest_party_id,
            job_id=job_id, headers=headers, overall_timeout=timeout,
            source_host=source_host, source_port=source_port
        )
        _routing_metadata = gen_routing_metadata(
            src_party_id=src_party_id, dest_party_id=dest_party_id,
        )
        for t in range(try_times):
            channel, stub = get_proxy_channel(host, port)

            try:
                _return, _call = stub.unaryCall.with_call(
                    _packet, metadata=_routing_metadata,
                    timeout=timeout or None,
                )
            except Exception as e:
                if t >= try_times - 1:
                    raise e
            else:
                try:
                    return json.loads(bytes.decode(_return.body.value))
                except Exception:
                    raise RuntimeError(f"{_return}, {_call}")
            finally:
                channel.close()


class BaseAPI:
    def __init__(self, client: APIClient, callback=None):
        self.client = client
        self.callback = callback

    def federated_command(self, job_id, src_role, src_party_id, dest_role, dest_party_id, endpoint, body,
                          federated_response, method='POST', only_scheduler=False, extra_params=None,
                          initiator_party_id=""):
        try:
            headers = {}
            if self.callback:
                result = self.callback(dest_party_id, body, initiator_party_id=initiator_party_id)
                if result.code == 0:
                    headers = result.signature if result.signature else {}
                else:
                    raise Exception(result.code, result.message)
            headers.update({"initiator-party-id": initiator_party_id})
            response = self.client.remote(job_id=job_id,
                                          method=method,
                                          endpoint=endpoint,
                                          src_role=src_role,
                                          src_party_id=src_party_id,
                                          dest_party_id=dest_party_id,
                                          json_body=body if body else {},
                                          extra_params=extra_params,
                                          is_local=self.is_local(party_id=dest_party_id),
                                          headers=headers)
            if only_scheduler:
                return response
        except Exception as e:
            response = {
                "code": FEDERATED_ERROR,
                "message": "Federated schedule error, {}".format(e)
            }
        if only_scheduler:
            return response
        federated_response[dest_role][dest_party_id] = response

    @staticmethod
    def is_local(party_id):
        return party_id == "0"

    def job_command(self, job_id, roles, command, command_body=None, parallel=False, initiator_party_id=""):
        federated_response = {}
        api_type = "partner/job"
        threads = []
        if not command_body:
            command_body = {}
        for party in roles:
            dest_role = party.get("role")
            dest_party_ids = party.get("party_id")
            federated_response[dest_role] = {}
            for dest_party_id in dest_party_ids:
                endpoint = f"/{api_type}/{command}"
                command_body["role"] = dest_role
                command_body["party_id"] = dest_party_id
                command_body["job_id"] = job_id
                args = (job_id, "", "", dest_role, dest_party_id, endpoint, command_body, federated_response)
                kwargs = {"initiator_party_id": initiator_party_id}
                if parallel:
                    t = threading.Thread(target=self.federated_command, args=args, kwargs=kwargs)
                    threads.append(t)
                    t.start()
                else:
                    self.federated_command(*args, initiator_party_id=initiator_party_id)
        for thread in threads:
            thread.join()
        return federated_response

    def task_command(self, tasks, command, command_body=None, parallel=False):
        federated_response = {}
        threads = []
        if not command_body:
            command_body = {}
        for task in tasks:
            command_body.update({
                "job_id": task["job_id"],
                "role": task["role"],
                "party_id": task["party_id"],
                "task_id": task["task_id"],
                "task_version": task["task_version"]
            })
            dest_role, dest_party_id = task["role"], task["party_id"]
            federated_response[dest_role] = federated_response.get(dest_role, {})
            endpoint = f"/partner/task/{command}"
            args = (task['job_id'], task['role'], task['party_id'], dest_role, dest_party_id, endpoint, command_body,
                    federated_response)
            if parallel:
                t = threading.Thread(target=self.federated_command, args=args)
                threads.append(t)
                t.start()
            else:
                self.federated_command(*args)
        for thread in threads:
            thread.join()
        return federated_response

    def scheduler_command(self, command, party_id, command_body=None, method='POST', initiator_party_id=""):
        try:
            federated_response = {}
            endpoint = f"/scheduler/{command}"
            response = self.federated_command(job_id="",
                                              method=method,
                                              endpoint=endpoint,
                                              src_role="",
                                              src_party_id="",
                                              dest_role="",
                                              dest_party_id=party_id,
                                              body=command_body if command_body else {},
                                              federated_response=federated_response,
                                              only_scheduler=True,
                                              initiator_party_id=initiator_party_id
                                              )
        except Exception as e:
            response = {
                "code": FEDERATED_ERROR,
                "message": "Federated schedule error, {}".format(e)
            }
        return response
