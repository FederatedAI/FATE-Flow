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
    def report_task_status(self, status, execution_id, error=None):
        endpoint = '/worker/task/status'
        return self.client.post(endpoint=endpoint, json={
            "status": status,
            "execution_id": execution_id,
            "error": error
        })

    def query_task_status(self, execution_id):
        endpoint = '/worker/task/status'
        return self.client.get(endpoint=endpoint, json={
            "execution_id": execution_id,
        })

    def log_output_artifacts(self, execution_id, type, output_key, uri, meta_data):
        return self.client.post(endpoint="/worker/task/output/tracking", json={
            "execution_id": execution_id,
            "type": type,
            "output_key": output_key,
            "uri": uri,
            "meta_data": meta_data
        })
