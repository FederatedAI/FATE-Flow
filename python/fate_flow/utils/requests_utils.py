#
#  Copyright 2021 The FATE Authors. All Rights Reserved.
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
import functools
import json
import requests

from fate_flow.utils.base_utils import CustomJSONEncoder

requests.models.complexjson.dumps = functools.partial(json.dumps, cls=CustomJSONEncoder)


def request(**kwargs):
    sess = requests.Session()
    stream = kwargs.pop('stream', sess.stream)
    timeout = kwargs.pop('timeout', None)
    if kwargs.get('headers'):
        kwargs['headers'] = {k.replace('_', '-').upper(): v for k, v in kwargs.get('headers', {}).items()}
    prepped = requests.Request(**kwargs).prepare()
    return sess.send(prepped, stream=stream, timeout=timeout)
