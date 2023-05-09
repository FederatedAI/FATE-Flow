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


@DB.connection_context()
def rerun_signal(job_id, set_or_reset: bool):
    if set_or_reset is True:
        update_fields = {ScheduleJob.f_rerun_signal: True, ScheduleJob.f_cancel_signal: False, ScheduleJob.f_end_scheduling_updates: 0}
    elif set_or_reset is False:
        update_fields = {ScheduleJob.f_rerun_signal: False}
    else:
        raise RuntimeError(f"can not support rereun signal {set_or_reset}")
    update_status = ScheduleJob.update(update_fields).where(ScheduleJob.f_job_id == job_id).execute() > 0
    return update_status


@DB.connection_context()
def schedule_signal(job_id: object, set_or_reset: bool, ready_timeout_ttl: object = None) -> object:
    filters = [ScheduleJob.f_job_id == job_id]
    if set_or_reset:
        update_fields = {ScheduleJob.f_schedule_signal: True, ScheduleJob.f_schedule_time: current_timestamp()}
        filters.append(ScheduleJob.f_schedule_signal == False)
    else:
        update_fields = {ScheduleJob.f_schedule_signal: False, ScheduleJob.f_schedule_time: None}
        filters.append(ScheduleJob.f_schedule_signal == True)
        if ready_timeout_ttl:
            filters.append(current_timestamp() - ScheduleJob.f_schedule_time > ready_timeout_ttl)
    update_status = ScheduleJob.update(update_fields).where(*filters).execute() > 0
    return update_status
