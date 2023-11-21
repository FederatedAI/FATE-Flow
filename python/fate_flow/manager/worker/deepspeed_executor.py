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
import json
import logging
import sys

from fate_flow.controller.task import TaskController
from fate_flow.entity.types import TaskStatus
from fate_flow.manager.worker.deepspeed_submit import DeepspeedSubmit
from fate_flow.utils.log_utils import schedule_logger


class Submit(object):
    def run(self, args):
        task_info = json.loads(args.task_info)
        job_id = task_info.get("job_id")
        try:

            from eggroll.deepspeed.submit import client
            client = client.DeepspeedJob(session_id=args.session_id)
            schedule_logger(job_id).info(f"start submit deepspeed task {args.session_id}")
            schedule_logger(job_id).info(f"submit config {args.config}")
            with open(args.task_config, "r") as f:
                task_conf = json.load(f)

            env_name = "FATE_TASK_CONFIG"

            options = {
                "eggroll.container.deepspeed.script.path": sys.modules[DeepspeedSubmit.__module__].__file__
            }
            resource_options = {"timeout_seconds": args.timeout, "resource_exhausted_strategy": "waiting"}
            client.submit(
                world_size=args.world_size,
                command_arguments=["--env-name", env_name],
                environment_variables={env_name: json.dumps(task_conf)},
                files={},
                resource_options=resource_options,
                options=options
            )
            schedule_logger(job_id).info(f"submit deepspeed task success")

            # threads = []
            # for handle in logger.handlers:
            #     handle.setFormatter(logging.Formatter("%(message)s"))
            # for _type in ["DEBUG", "INFO", "ERROR"]:
            #     threads.extend(
            #         client.write_logs_to(log_type=_type, logging=getattr(logger, _type.lower()))
            #     )
            # for thread in threads:
            #     thread.join()
        except Exception as e:
            schedule_logger(job_id).exception(e)
            task_info["party_status"] = TaskStatus.FAILED
            TaskController.update_task_status(task_info=task_info)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--world_size', required=False, type=str, help="world size")
    parser.add_argument('--task_config', required=False, type=str, help="session id")

    parser.add_argument('--task_info', required=False, type=str, help="task info")
    parser.add_argument('--session_id', required=False, type=str, help="session id")
    parser.add_argument('--timeout', required=False, type=int, help="timeout")
    args = parser.parse_args()
    Submit().run(args)
