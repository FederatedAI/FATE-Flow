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
from .._base import BaseEntity


class FlowInstance(BaseEntity):
    def __init__(self, **kwargs):
        self.instance_id = None,
        self.timestamp = None,
        self.version = None,
        self.host = None,
        self.grpc_port = None,
        self.http_port = None
        for k, v in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)

    def to_dict(self):
        d = {}
        for k, v in self.__dict__.items():
            if v is None:
                continue
            d[k] = v
        return d

    @property
    def grpc_address(self):
        return f'{self.host}:{self.grpc_port}'

    @property
    def http_address(self):
        return f'{self.host}:{self.http_port}'
