
from .runtime_config import CommonRuntimeConfig


class CommonFederated:

    @classmethod
    def create_job(cls, command_body):
        return CommonRuntimeConfig.SCHEDULE_CLIENT.federated.create_job(
            command_body=command_body, method="post")

    @classmethod
    def query_job(cls, command_body):

        return CommonRuntimeConfig.SCHEDULE_CLIENT.federated.query_job(
            command_body=command_body, method="post")

    @classmethod
    def query_job_batch(cls, command_body):

        return CommonRuntimeConfig.SCHEDULE_CLIENT.federated.query_batch_job(
            command_body=command_body, method="get")

    @classmethod
    def delete_job(cls, command_body):

        return CommonRuntimeConfig.SCHEDULE_CLIENT.federated.delete_job(
            command_body=command_body, method="post")

    @classmethod
    def stop_job(cls, command_body):
        return CommonRuntimeConfig.SCHEDULE_CLIENT.federated.stop_job(
            command_body=command_body, method="post")