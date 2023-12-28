from fate_flow.adapter.bfia.utils.entity.status import TaskStatus, JobStatus, EndStatus
from fate_flow.db import ScheduleJob, Task
from fate_flow.entity.types import PROTOCOL
from fate_flow.manager.operation.job_saver import JobSaver, ScheduleJobSaver


class BfiaJobSaver(JobSaver):
    @classmethod
    def check_task_status(cls, old_status, dest_status):
        return TaskStatus.StateTransitionRule.if_pass(src_status=old_status, dest_status=dest_status)

    @classmethod
    def check_job_status(cls, old_status, dest_status):
        return JobStatus.StateTransitionRule.if_pass(src_status=old_status, dest_status=dest_status)

    @classmethod
    def end_status_contains(cls, status):
        return EndStatus.contains(status)

    @classmethod
    def query_task(cls, only_latest=True, reverse=None, order_by=None, protocol=PROTOCOL.BFIA, **kwargs):
        return cls._query_task(
            Task, only_latest=only_latest, reverse=reverse, order_by=order_by, protocol=protocol, **kwargs
        )


class BfiaScheduleJobSaver(ScheduleJobSaver, BfiaJobSaver):
    @classmethod
    def query_job(cls, reverse=None, order_by=None, protocol=PROTOCOL.BFIA, **kwargs):
        return cls._query_job(ScheduleJob, reverse, order_by, protocol=protocol, **kwargs)
