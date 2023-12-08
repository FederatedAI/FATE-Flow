from fate_flow.adapter._loader import load_bridge_module
from fate_flow.entity.spec.flow import SubmitJobInput, SubmitJobOutput, QueryJobInput, QueryJobOutput, StopJobInput, \
    StopJobOutput, QueryTaskOutput, QueryTaskInput


class AdapterJobController(object):
    def __init__(self, protocol_name):
        packages = load_bridge_module(protocol_name=protocol_name)
        self.controller_adapter = getattr(packages, "JobController")

    def create_job(self, submit_job_input: SubmitJobInput) -> SubmitJobOutput:
        return self.controller_adapter.create_job(submit_job_input)

    def query_job(self, query_job_input: QueryJobInput) -> QueryJobOutput:
        return self.controller_adapter.query_job(query_job_input)

    def stop_job(self, stop_job_input: StopJobInput) -> StopJobOutput:
        return self.controller_adapter.stop_job(stop_job_input)

    def query_task(self, query_task_input: QueryTaskInput) -> QueryTaskOutput:
        return self.controller_adapter.query_task(query_task_input)

    def rerun_job(self):
        pass

    @staticmethod
    def query_output_data():
        return {}

    @staticmethod
    def query_output_model():
        return {}

    @staticmethod
    def query_output_metric():
        return {}
