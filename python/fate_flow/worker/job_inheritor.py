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
import traceback

from fate_flow.controller.job_controller import JobController
from fate_flow.entity.run_status import JobInheritanceStatus
from fate_flow.operation.job_saver import JobSaver
from fate_flow.utils.log_utils import getLogger
from fate_flow.worker.base_worker import BaseWorker

LOGGER = getLogger()


class JobInherit(BaseWorker):
    def _run(self):
        job = JobSaver.query_job(job_id=self.args.job_id, role=self.args.role, party_id=self.args.party_id)[0]
        try:
            JobController.job_reload(job)
        except Exception as e:
            traceback.print_exc()
            JobSaver.update_job(job_info={"job_id": job.f_job_id, "role": job.f_role, "party_id": job.f_party_id,
                                          "inheritance_status": JobInheritanceStatus.FAILED})
            LOGGER.exception(e)


if __name__ == '__main__':
    JobInherit().run()
