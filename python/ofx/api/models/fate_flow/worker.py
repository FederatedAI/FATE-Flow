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
        if not error:
            error = ""
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

    def save_model(self, model_id, model_version, execution_id, output_key, type_name, fp):
        files = {"file": fp}
        return self.client.send_file(
            endpoint="/worker/model/save",
            files=files,
            data={
                "model_id": model_id,
                "model_version": model_version,
                "execution_id": execution_id,
                "output_key": output_key,
                "type_name": type_name
            })

    def save_data_tracking(self, execution_id, output_key, meta_data, uri, namespace, name, overview, source, data_type,
                           index, partitions=None):
        return self.client.post(
            endpoint="/worker/data/tracking/save",
            json={
                "execution_id": execution_id,
                "output_key": output_key,
                "meta_data": meta_data,
                "uri": uri,
                "namespace": namespace,
                "name": name,
                "overview": overview,
                "source": source,
                "data_type": data_type,
                "index": index,
                "partitions": partitions
            })

    def query_data_meta(self, job_id=None, role=None, party_id=None, task_name=None, output_key=None, namespace=None,
                        name=None):
        # [job_id, role, party_id, task_name, output_key] or [name, namespace]
        if namespace and name:
            params = {
                    "namespace": namespace,
                    "name": name
            }
        else:
            params = {
                "job_id": job_id,
                "role": role,
                "party_id": party_id,
                "task_name": task_name,
                "output_key": output_key
            }
        return self.client.get(
            endpoint="/worker/data/tracking/query",
            params=params
        )

    def download_model(self, model_id, model_version, task_name, output_key, role, party_id):
        return self.client.get(
            endpoint="/worker/model/download",
            params={
                "model_id": model_id,
                "model_version": model_version,
                "task_name": task_name,
                "output_key": output_key,
                "role": role,
                "party_id": party_id
            }
        )

    def save_metric(self, execution_id, data):
        return self.client.post(
            endpoint="/worker/metric/save",
            json={
                "execution_id": execution_id,
                "data": data
            })

    def get_metric_save_url(self, execution_id):
        endpoint = f"/worker/metric/save/{execution_id}"
        return f"{self.client.url}{endpoint}"
