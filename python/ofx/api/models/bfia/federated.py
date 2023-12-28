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


class Federated(BaseAPI):
    def create_job(self, node_list, command_body):
        return self.job_command(
            node_list=node_list,
            command_body=command_body,
            parallel=False,
            endpoint="/v1/interconn/schedule/job/create"
        )

    def start_job(self, node_list, command_body):
        return self.job_command(
            node_list=node_list,
            command_body=command_body,
            parallel=False,
            endpoint="/v1/interconn/schedule/job/start"
        )

    def stop_job(self, node_list, command_body):
        return self.job_command(
            node_list=node_list,
            command_body=command_body,
            parallel=False,
            endpoint="/v1/interconn/schedule/job/stop"
        )

    def start_task(self, node_list, command_body):
        return self.job_command(
            node_list=node_list,
            command_body=command_body,
            parallel=False,
            endpoint="/v1/interconn/schedule/task/start"
        )

    def poll_task(self, node_list, command_body):
        return self.job_command(
            node_list=node_list,
            command_body=command_body,
            parallel=False,
            endpoint="/v1/interconn/schedule/task/poll"
        )
