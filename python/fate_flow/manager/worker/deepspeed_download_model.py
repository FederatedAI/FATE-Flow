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

from fate_flow.engine.devices import build_engine
from fate_flow.entity.types import LauncherType
from fate_flow.manager.operation.job_saver import JobSaver
from fate_flow.utils.log_utils import schedule_logger


class DownloadModel(object):
    def run(self, args):
        deepspeed_engine = build_engine(args.provider_name, LauncherType.DEEPSPEED)
        tasks = JobSaver.query_task(
            task_id=self.args.task_id,
            task_version=self.args.task_version,
            job_id=self.args.job_id,
            role=self.args.role,
            party_id=self.args.party_id
        )
        task = tasks[0]
        schedule_logger(self.args.job_id).info("start download model")
        deepspeed_engine.download_model_do(task)
        schedule_logger(self.args.job_id).info("download model success")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--provider_name', required=True, type=str, help="provider name")
    parser.add_argument('--job_id', required=True, type=str, help="job id")
    parser.add_argument('--role', required=True, type=str, help="role")
    parser.add_argument('--party_id', required=True, type=str, help="party id")
    parser.add_argument('--task_id', required=True, type=str, help="task id")
    parser.add_argument('--task_version', required=True, type=int, help="task version")


    args = parser.parse_args()
    DownloadModel().run(args)
