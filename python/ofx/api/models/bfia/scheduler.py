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


class Scheduler(BaseAPI):
    def create_job(self, party_id, command_body):
        return self.scheduler_command(
            endpoint="/v1/interconn/schedule/job/create_all",
            node_id=party_id,
            command_body=command_body
        )

    def audit_confirm(self, party_id, command_body):
        return self.scheduler_command(
            endpoint="/v1/interconn/schedule/job/audit_confirm",
            node_id=party_id,
            command_body=command_body
        )

    def stop_job(self, party_id, command_body):
        return self.scheduler_command(
            endpoint="/v1/interconn/schedule/job/stop_all",
            node_id=party_id,
            command_body=command_body
        )

    def report_task(self, party_id, command_body):
        return self.scheduler_command(
            endpoint="/v1/interconn/schedule/task/callback",
            node_id=party_id,
            command_body=command_body
        )




