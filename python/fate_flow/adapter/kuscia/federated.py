
from .runtime_config import KusciaRuntimeConfig


class Federated:

    @classmethod
    def create_job(cls, command_body):
        response = KusciaRuntimeConfig.SCHEDULE_CLIENT.remote_on_http(
            method="post",
            endpoint="CreateJob",
            command_body=command_body,)
        return response

    @classmethod
    def query_job(cls, command_body):
        response = KusciaRuntimeConfig.SCHEDULE_CLIENT.remote_on_http(
            method="post",
            endpoint="QueryJob",
            command_body=command_body)
        return response

    @classmethod
    def query_job_batch(cls, command_body):
        response = KusciaRuntimeConfig.SCHEDULE_CLIENT.remote_on_http(
            method="post",
            endpoint="QueryBatchJob",
            command_body=command_body)
        return response

    @classmethod
    def delete_job(cls, command_body):
        response = KusciaRuntimeConfig.SCHEDULE_CLIENT.remote_on_http(
            method="post",
            endpoint="DeleteJob",
            command_body=command_body)
        return response

    @classmethod
    def stop_job(cls, command_body):
        response = KusciaRuntimeConfig.SCHEDULE_CLIENT.remote_on_http(
            method="post",
            endpoint="StopJob",
            command_body=command_body)
        return response