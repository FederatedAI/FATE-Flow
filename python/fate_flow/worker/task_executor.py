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
import argparse

from fate_flow.entity import BaseEntity
from fate_flow.utils.log import getLogger

LOGGER = getLogger()


class WorkerArgs(BaseEntity):
    def __init__(self, **kwargs):
        self.job_id = kwargs.get("job_id")
        self.task_name = kwargs.get("task_name")
        self.task_id = kwargs.get("task_id")
        self.task_version = kwargs.get("task_version")
        self.role = kwargs.get("role")
        self.party_id = kwargs.get("party_id")


class TaskExecutor:
    def __init__(self):
        self.args: WorkerArgs = None
        self.run_pid = None
        self.report_info = {}

    def run(self):
        self.args = self.get_args()
        self.report_info.update({
            "job_id": self.args.job_id,
            "task_id": self.args.task_id,
            "task_version": self.args.task_version,
            "role": self.args.role,
            "party_id": self.args.party_id,
            "status": "success"
        })
        LOGGER.info("task test success")

    @staticmethod
    def get_args(**kwargs):
        if kwargs:
            return WorkerArgs(**kwargs)
        else:
            parser = argparse.ArgumentParser()
            for arg in WorkerArgs().to_dict():
                parser.add_argument(f"--{arg}", required=False)
            return WorkerArgs(**parser.parse_args().__dict__)

    def report_task_info_to_driver(self):
        LOGGER.info(f"report info: {self.report_info}")
        import requests
        url = "http://127.0.0.1:9380/v2/worker/task/report"
        response = requests.post(url, json=self.report_info)
        LOGGER.info(response.text)

if __name__ == '__main__':
    worker = TaskExecutor()
    worker.run()
    worker.report_task_info_to_driver()

