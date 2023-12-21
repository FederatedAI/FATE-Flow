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
import logging

from fate_arch.common.log import getLogger
from fate_flow.db.runtime_config import RuntimeConfig
from fate_flow.entity.run_status import TaskStatus
from fate_flow.scheduling_apps.client import ControllerClient
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

            logger = getLogger()
            threads = []
            for handle in logger.handlers:
                handle.setFormatter(logging.Formatter("%(message)s"))
            for _type in ["DEBUG", "INFO", "ERROR"]:
                threads.extend(
                    client.write_logs_to(log_type=_type, logging=getattr(logger, _type.lower()))
                )
            for thread in threads:
                thread.join()
        except Exception as e:
            task_info = {
                "job_id": self.args.job_id,
                "role": self.args.role,
                "party_id": self.args.party_id,
                "task_id": self.args.task_id,
                "task_version": self.args.task_version,
                "component_name": self.args.component_name,
                "party_status": TaskStatus.FAILED,
            }

            RuntimeConfig.init_config(JOB_SERVER_HOST=self.args.job_server.split(':')[0], HTTP_PORT=self.args.job_server.split(':')[1])
            ControllerClient.report_task(task_info)
            schedule_logger(self.args.job_id).exception(e)


if __name__ == "__main__":
    Submit().run()
