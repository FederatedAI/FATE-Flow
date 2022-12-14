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
from fate_flow.db.base_models import DB
from fate_flow.db.schedule_models import ScheduleJob
from fate_flow.utils.base_utils import current_timestamp


@DB.connection_context()
def cancel_signal(job_id, set_or_reset: bool):
    update_status = ScheduleJob.update({ScheduleJob.f_cancel_signal: set_or_reset, ScheduleJob.f_cancel_time: current_timestamp()}).where(ScheduleJob.f_job_id == job_id).execute() > 0
    return update_status
