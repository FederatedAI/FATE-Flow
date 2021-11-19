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

import requests

from fate_flow.utils.log_utils import getLogger
from fate_flow.entity import RetCode
from fate_flow.entity.run_status import TaskStatus
from fate_flow.scheduling_apps.client import ControllerClient
from fate_flow.settings import HEADERS
from fate_flow.utils.decorators import trys
from fate_flow.worker.base_worker import BaseWorker

LOGGER = getLogger()


class ComponentInput:
    def __init__(
            self,
            tracker,
            checkpoint_manager,
            task_version_id,
            parameters,
            datasets,
            models,
            caches,
            job_parameters,
            roles,
            flow_feeded_parameters,
    ) -> None:
        self._tracker = tracker
        self._checkpoint_manager = checkpoint_manager
        self._task_version_id = task_version_id
        self._parameters = parameters
        self._datasets = datasets
        self._models = models
        self._caches = caches
        self._job_parameters = job_parameters
        self._roles = roles
        self._flow_feeded_parameters = flow_feeded_parameters

    @property
    def tracker(self):
        return self._tracker

    @property
    def task_version_id(self):
        return self._task_version_id

    @property
    def checkpoint_manager(self):
        return self._checkpoint_manager

    @property
    def parameters(self):
        return self._parameters

    @property
    def flow_feeded_parameters(self):
        return self._flow_feeded_parameters

    @property
    def roles(self):
        return self._roles

    @property
    def job_parameters(self):
        return self._job_parameters

    @property
    def datasets(self):
        return self._datasets

    @property
    def models(self):
        return {k: v for k, v in self._models.items() if v is not None}

    @property
    def caches(self):
        return self._caches


class BaseTaskWorker(BaseWorker):
    def _run(self):
        self.report_info.update({
            "job_id": self.args.job_id,
            "component_name": self.args.component_name,
            "task_id": self.args.task_id,
            "task_version": self.args.task_version,
            "role": self.args.role,
            "party_id": self.args.party_id,
            "run_ip": self.args.run_ip,
            "run_pid": self.run_pid
        })
        self._run_()

    def _run_(self):
        pass

    def _handle_exception(self):
        self.report_info["party_status"] = TaskStatus.FAILED
        self.report_task_info_to_driver()

    def report_task_info_to_driver(self):
        LOGGER.info("report {} {} {} {} {} to driver:\n{}".format(
            self.__class__.__name__,
            self.report_info["task_id"],
            self.report_info["task_version"],
            self.report_info["role"],
            self.report_info["party_id"],
            self.report_info
        ))
        ControllerClient.report_task(self.report_info)

    @trys(5)
    def request_data_exchange_proxy(self, endpoint, data, headers=None):
        http_port = 7000
        federation_proxy_remote_url = f"http://{self.args.run_ip}:{http_port}{endpoint}"
        if headers:
            response = requests.post(federation_proxy_remote_url, data=data, headers=headers)
        else:
            response = requests.post(federation_proxy_remote_url, json=data, headers=HEADERS)
        if response.status_code not in {200, 201}:
            raise Exception(
                f"request proxy url {federation_proxy_remote_url} error, response code: {response.status_code}")
        response_dict = response.json()
        if response_dict["retcode"] != RetCode.SUCCESS:
            raise Exception(f"request proxy url {federation_proxy_remote_url} error, response: {response_dict}")
        return response_dict
