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
import abc
from typing import Dict


class JobSchedulerABC:
    @classmethod
    def submit(cls, dag_schema) -> Dict:
        """
        description：
            Create a job to all parties and set the job status to waiting
        :param dag_schema: job config;

        """

    @abc.abstractmethod
    def run_do(self):
        """
        description：
            Scheduling various status job, including: waiting、running、ready、rerun、end、etc.
        """

    @classmethod
    def stop_job(cls, job_id: str, stop_status: str):
        """
        description：
            Stop a job to all parties and set the job status to end status
        :param job_id: job id
        :param stop_status: In which state to stop the task.

        """

    @classmethod
    def rerun_job(cls, job_id: str, auto: bool, tasks=None):
        """
        description：
            rerun a job
        :param job_id: job id
        :param auto: Whether the scheduler automatically rerun
        :param tasks: Specified rerun task list.

        """

    @classmethod
    def adapt_party_parameters(cls, dag_schema, role):
        """
        """

    @classmethod
    def check_job_parameters(cls, dag_schema, is_local):
        """
        """
