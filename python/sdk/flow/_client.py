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
from .api import Job, Task
from .utils.base_utils import BaseFlowClient


class FlowClient(BaseFlowClient):
    job = Job()
    task = Task()

    def __init__(self, ip="127.0.0.1", port=9380, version="v2", app_id=None, app_token=None, user_name=""):
        super().__init__(ip, port, version, app_id=app_id, app_token=app_token, user_name=user_name)
        self.API_BASE_URL = 'http://%s:%s/%s' % (ip, port, version)
