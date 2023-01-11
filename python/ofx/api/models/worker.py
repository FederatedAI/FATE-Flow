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
from .resource import BaseAPI


class Worker(BaseAPI):

    def task_parameters(self, task_info):
        endpoint = '/party/{}/{}/{}/{}/{}/{}/report'.format(
            task_info["job_id"],
            task_info["component_name"],
            task_info["task_id"],
            task_info["task_version"],
            task_info["role"],
            task_info["party_id"]
        )
        return self.client.post(endpoint=endpoint, json=task_info)

    def report_task(self, task_info):
        endpoint = '/party/{}/{}/{}/{}/{}/{}/report'.format(
            task_info["job_id"],
            task_info["component_name"],
            task_info["task_id"],
            task_info["task_version"],
            task_info["role"],
            task_info["party_id"]
        )
        return self.client.post(endpoint=endpoint, json=task_info)

    def output_metric(self, content):
        return self.client.post(endpoint="/worker/metric/write", json=content)

    def write_model(self, content):
        return self.client.post(endpoint="/worker/model/write", json=content)
