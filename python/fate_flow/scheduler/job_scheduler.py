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
from pydantic import typing

from fate_flow.runtime.runtime_config import RuntimeConfig
from fate_flow.db.schedule_models import ScheduleTaskStatus
from fate_flow.utils.cron import Cron


class DAGScheduler(Cron):
    @classmethod
    def submit(cls, dag_schema):
        return RuntimeConfig.SCHEDULER.submit(dag_schema)

    def run_do(self):
        return RuntimeConfig.SCHEDULER.run_do()

    @classmethod
    def stop_job(cls, job_id, stop_status):
        return RuntimeConfig.SCHEDULER.stop_job(job_id, stop_status)

    @classmethod
    def rerun_job(cls, job_id, auto, tasks: typing.List[ScheduleTaskStatus] = None):
        return RuntimeConfig.SCHEDULER.rerun_job(job_id, auto, tasks)
