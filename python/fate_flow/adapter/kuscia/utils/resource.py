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


import requests
import importlib

from ofx.api.models.fate_flow.resource import APIClient

FEDERATED_ERROR = 104


class KusciaApiClient(APIClient):

    def __init__(self, client_cert=None, client_key=None, veritfy=None, token=None, restful=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client_cert = client_cert
        self.client_key = client_key
        self.veritfy = veritfy
        self.token = token
        self.restful = restful

    @property
    def base_url(self):
        return f'{self.protocol}://{self.remote_host}:{self.remote_port}'

    def generate_endpoint(self, endpoint):
        if self.restful and self.version:
            endpoint = f"/api/{self.version}/job/{endpoint}"
        return endpoint

    def remote_on_http(self, method, endpoint, try_times=3, timeout=10, json_body=None, **kwargs):
        if not self.remote_host and not self.remote_port:
            raise Exception(
                f'{self.remote_protocol} coordination communication protocol need remote host and remote port.')
        package = f"fate_flow.adapt.kuscia.settings"
        _url = getattr(importlib.import_module(package), "URLS")
        endpoint = _url[endpoint]
        url = self.base_url + endpoint

        for t in range(try_times):
            try:
                if self.client_cert and self.client_key and self.veritfy:
                    response = requests.request(method=method, url=url, cert=(self.client_cert, self.client_key),
                                                veritfy=self.veritfy, timeout=timeout, json=json_body,
                                                headers={"token": self.token})
                else:
                    response = requests.request(method=method, url=url, timeout=timeout, json=json_body)
                response.raise_for_status()
            except Exception as e:
                if t >= try_times - 1:
                    raise e
            else:
                try:
                    return response.json()
                except:
                    raise Exception(response.text)





