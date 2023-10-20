from fate_flow.entity.types import BaseStateTransitionRule, BaseStatus


class StatusSet(BaseStatus):
    PENDING = "PENDING"
    READY = 'READY'
    RUNNING = "RUNNING"
    FINISHED = "FINISHED"
    REJECTED = "REJECTED"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"

    @classmethod
    def get_level(cls, status):
        return dict(zip(cls.status_list(), range(len(cls.status_list())))).get(status, None)


class JobStatus(BaseStatus):
    PENDING = StatusSet.PENDING
    READY = StatusSet.READY
    REJECTED = StatusSet.REJECTED
    RUNNING = StatusSet.RUNNING
    FINISHED = StatusSet.FINISHED

    class StateTransitionRule(BaseStateTransitionRule):
        RULES = {
            StatusSet.PENDING: [StatusSet.READY, StatusSet.REJECTED],
            StatusSet.READY: [StatusSet.RUNNING, StatusSet.FINISHED],
            StatusSet.RUNNING: [StatusSet.FINISHED],
            StatusSet.FINISHED: []
        }


class TaskStatus(BaseStatus):
    PENDING = StatusSet.PENDING
    READY = StatusSet.READY
    RUNNING = StatusSet.RUNNING
    SUCCESS = StatusSet.SUCCESS
    FAILED = StatusSet.FAILED

    class StateTransitionRule(BaseStateTransitionRule):
        RULES = {
            StatusSet.PENDING: [StatusSet.READY, StatusSet.RUNNING, StatusSet.SUCCESS, StatusSet.FAILED],
            StatusSet.READY: [StatusSet.RUNNING, StatusSet.FAILED, StatusSet.SUCCESS],
            StatusSet.RUNNING: [StatusSet.SUCCESS, StatusSet.FAILED],
            StatusSet.FAILED: [],
            StatusSet.SUCCESS: [],
        }


class EndStatus(BaseStatus):
    FAILED = StatusSet.FAILED
    FINISHED = StatusSet.FINISHED
    SUCCESS = StatusSet.SUCCESS


class InterruptStatus(BaseStatus):
    FAILED = StatusSet.FAILED
