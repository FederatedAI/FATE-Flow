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
#
import hashlib
import inspect
import json
import random
import sys
import time
import traceback

import requests


def _is_api_endpoint(obj):
    return isinstance(obj, BaseFlowAPI)

class BaseFlowClient:
    API_BASE_URL = ''

    def __new__(cls, *args, **kwargs):
        self = super().__new__(cls)
        api_endpoints = inspect.getmembers(self, _is_api_endpoint)
        for name, api in api_endpoints:
            api_cls = type(api)
            api = api_cls(self)
            setattr(self, name, api)
        return self

    def __init__(self, ip, port, version, app_id=None, app_token=None, user_name=""):
        self._http = requests.Session()
        self.ip = ip
        self.port = port
        self.version = version

        self.app_id = app_id if app_id and app_id else None
        self.app_token = app_token if app_token and app_token else None
        self.user_name = user_name

    def _request(self, method, uri, **kwargs):
        stream = kwargs.pop('stream', self._http.stream)
        prepped = requests.Request(method, self.API_BASE_URL + uri, **kwargs).prepare()

        if self._signature_headers:
            prepped.headers.update(self._signature_headers)

        try:
            response = self._http.send(prepped, stream=stream)
        except Exception as e:
            response = {
                'retcode': 100,
                'retmsg': str(e),
            }

            if 'connection refused' in response['retmsg'].lower():
                response['retmsg'] = 'Connection refused, Please check if the fate flow service is started'
            else:
                exc_type, exc_value, exc_traceback_obj = sys.exc_info()
                response['traceback'] = traceback.format_exception(exc_type, exc_value, exc_traceback_obj)

        return response

    @staticmethod
    def _decode_result(response):
        try:
            result = json.loads(response.content.decode('utf-8', 'ignore'), strict=False)
        except (TypeError, ValueError):
            return response
        else:
            return result

    def _handle_result(self, response):
        if isinstance(response, requests.models.Response):
            return response.json()
        elif isinstance(response, dict):
            return response
        else:
            return self._decode_result(response)

    @property
    def _signature_headers(self):
        if self.app_id and self.app_token:
            nonce, timestamp, sign = self.generate_signature_params()
            return {
                "app_id": self.app_id,
                "user_name": self.user_name,
                "nonce": nonce,
                "timestamp": timestamp,
                "signature": sign
            }
        else:
            return {}

    def generate_signature_params(self):
        nonce = str(random.randint(10000, 99999))
        timestamp = str(int(time.time()))
        temp = hashlib.md5(str(self.app_id + self.user_name + nonce + timestamp).encode("utf8")).hexdigest().lower()
        sign = hashlib.md5(str(temp + self.app_token).encode("utf8")).hexdigest().lower()
        return nonce, timestamp, sign

    def get(self, uri, **kwargs):
        return self._request(method='get', uri=uri, **kwargs)

    def post(self, uri, **kwargs):
        return self._request(method='post', uri=uri, **kwargs)


class BaseFlowAPI:
    def __init__(self, client=None):
        self._client = client

    def _get(self, url, handle_result=True, **kwargs):
        if handle_result:
            return self._handle_result(self._client.get(url, **kwargs))
        else:
            return self._client.get(url, **kwargs)

    def _post(self, url, handle_result=True, **kwargs):
        if handle_result:
            return self._handle_result(self._client.post(url, **kwargs))
        else:
            return self._client.post(url, **kwargs)

    def _handle_result(self, response):
        return self._client._handle_result(response)

    @property
    def session(self):
        return self._client.session

    @property
    def ip(self):
        return self._client.ip

    @property
    def port(self):
        return self._client.port

    @property
    def version(self):
        return self._client.version