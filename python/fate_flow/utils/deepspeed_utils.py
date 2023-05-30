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
import os
import sys

from fate_flow.utils.log_utils import schedule_logger
from fate_flow.worker.base_worker import BaseWorker


class Submit(BaseWorker):
    def _run(self):
        try:
            from eggroll.deepspeed.submit import client
            client = client.DeepspeedJob(session_id=self.args.session_id)
            config = self.args.config
            schedule_logger(self.args.job_id).info(f"start submit deepspeed task {self.args.session_id}")
            schedule_logger(self.args.job_id).info(f"submit config {config}")
            client.submit(
                world_size=config.get("world_size"),
                command_arguments=config.get("command_arguments"),
                environment_variables=config.get("environment_variables"),
                files=config.get("files"),
                resource_options=config.get("resource_options"),
                options=config.get("options")
            )
            schedule_logger(self.args.job_id).info(f"submit deepspeed task success")
        except Exception as e:
            schedule_logger(self.args.job_id).exception(e)


if __name__ == "__main__":
    Submit().run()
