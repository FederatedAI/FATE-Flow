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
from typing import Dict, Union

from requests.models import Response

from ..utils.base_utils import BaseFlowAPI
from ..utils.io_utils import download_from_request
from ..utils.params_utils import filter_invalid_params


class Job(BaseFlowAPI):
    def submit(self, dag_schema: Dict):
        """
        Submit job

        Args:
            dag_schema: job config

        Returns:
        {"code":0,"data":{xxx},"job_id":"xxx","message":"success"}
        """
        return self._post(url='/job/submit', json={
            'dag_schema': dag_schema,
        })

    def query(self, job_id: str = None, role: str = None, party_id: str = None, status: str = None):
        """
        Query job details

        Args:
            job_id: job id.
            role: role, such as: "guest", "host"
            party_id: party id, such as: "9999", "10000"
            status: job status, such as: "success", "failed"

        Returns:
        {'code': 0, 'message': 'success', 'data': [{...}, {...}]
        """
        kwargs = locals()
        params = filter_invalid_params(**kwargs)
        return self._get(url='/job/query', params=params)

    def stop(self, job_id: str = None):
        """
        Stop job

        Args:
            job_id: job id.

        Returns:
        {'code': 0, 'message': 'success'}
        """
        kwargs = locals()
        data = filter_invalid_params(**kwargs)
        return self._post(url='/job/stop', json=data)

    def rerun(self, job_id: str = None):
        """
        You can try to rerun a job when it was failed

        Args:
            job_id: job id.

        Returns:
        {'code': 0, 'message': 'success'}
        """
        kwargs = locals()
        data = filter_invalid_params(**kwargs)
        return self._post(url='/job/rerun', json=data)

    def query_job_list(
            self,
            limit: int = None,
            page: int = None,
            job_id: str = None,
            description: str = None,
            party_id: str = None,
            role: str = None,
            status: str = None,
            order_by: str = None,
            order: str = None
    ):
        """
        Show job list on client job page，You can get the job list through this interface on your job page

        Args:
            limit: job count of per page， use with the parameter "page".
            page: job page num， use with the parameter "limit".
            job_id: fuzzy matching by job id.
            description: fuzzy matching by description.
            party_id: party id, such as: "9999", "10000"
            role:  role info, such as: "guest", "host", "arbiter"
            status: job status, such as: "success", "failed"
            order_by: sort by job field, default "create_time"
            order: default "desc"

        Returns:
            {"code": 0, "message": "success", "data": {"count": 100, "data": [{...}, {...}]}}
        """
        kwargs = locals()
        data = filter_invalid_params(**kwargs)
        return self._get(url='/job/list/query', params=data)

    def download_log(self, job_id: str, path: str = None) -> Union[str, Response]:
        """
        Download this job logs, If the parameter of "path" is passed, it will be downloaded to the local path,
        otherwise it will return "requests.models.Response"

        Args:
            job_id (str): job id,
            path (str): absolute path of download, such as: /data/projects/fate/fateflow/download/

        Returns:
            'requests.models.Response' if the parameter of "path" is passed and the request is successful;
            'str' if the parameter of "path" is not passed， such as: "download success, please check the path xxx"
        """
        kwargs = locals()
        _path = kwargs.pop("path", None)
        data = filter_invalid_params(**kwargs)
        resp = self._post(url='/job/log/download', handle_result=False, json=data)
        if _path:
            # download to local dir
            return download_from_request(resp, _path)
        else:
            # return data stream
            return resp

    def queue_clean(self):
        """
        Clean up the job queue: change the status of "waiting" jobs to "canceled"
        """
        return self._post(url='/job/queue/clean')
