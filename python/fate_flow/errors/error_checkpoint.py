from fate_flow.errors import FateFlowError

__all__ = ['CheckpointError']


class CheckpointError(FateFlowError):
    message = 'Unknown checkpoint error'
