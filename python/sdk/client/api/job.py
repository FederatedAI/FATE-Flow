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
from sdk.client.api.base import BaseFlowAPI
from sdk.client.utils.params_utils import filter_invalid_params


class Job(BaseFlowAPI):
    def submit(self, dag_schema):
        return self._post(url='job/submit', json={
            'dag_schema': dag_schema,
        })

    def query(self, job_id=None, role=None, party_id=None, status=None):
        kwargs = locals()
        params = filter_invalid_params(**kwargs)
        return self._get(url='job/query', params=params)

    def stop(self, job_id):
        kwargs = locals()
        data = filter_invalid_params(**kwargs)
        return self._post(url='job/stop', json=data)
