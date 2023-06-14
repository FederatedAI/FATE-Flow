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
    def report_task_status(self, status, execution_id, error=""):
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

    def save_model(self, model_id, model_version, execution_id, output_key, model_data, model_path):
        with open(model_path, 'rb') as fp:
            files = {"file": fp}
            return self.client.post(
                endpoint="/worker/output/save",
                files=files,
                json={
                    "model_id": model_id,
                    "model_version": model_version,
                    "execution_id": execution_id,
                    "output_key": output_key,
                    "model_meta": model_data
                })

    def save_data_tracking(self, execution_id, output_key, model_data, uri):
        return self.client.post(
            endpoint="/worker/data/tracking/save",
            json={
                "execution_id": execution_id,
                "output_key": output_key,
                "model_meta": model_data,
                "uri": uri
            })

    def query_data_tracking(self, job_id, role, party_id, task_name, output_key):
        return self.client.get(
            endpoint="/worker/data/tracking/query",
            params={
                "job_id": job_id,
                "role": role,
                "party_id": party_id,
                "task_name": task_name,
                "output_key": output_key
            })

    def save_metric(self, execution_id, data, incomplete):
        return self.client.post(
            endpoint="/worker/metric/save",
            json={
                "execution_id": execution_id,
                "data": data,
                "incomplete": incomplete
            })
