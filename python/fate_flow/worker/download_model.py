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
from fate_flow.controller.engine_adapt import build_engine
from fate_flow.operation.job_saver import JobSaver
from fate_flow.utils.log_utils import schedule_logger
from fate_flow.worker.base_worker import BaseWorker


class DownloadModel(BaseWorker):
    def _run(self):
        deepspeed_engine = build_engine(self.args.computing_engine, True)
        tasks = JobSaver.query_task(
            task_id=self.args.task_id,
            task_version=self.args.task_version,
            job_id=self.args.job_id,
            role=self.args.role,
            party_id=self.args.party_id
        )
        task = tasks[0]
        schedule_logger(self.args.job_id).info("start download model")
        deepspeed_engine.download_model(task)
        schedule_logger(self.args.job_id).info("download model success")


if __name__ == '__main__':
    DownloadModel().run()
