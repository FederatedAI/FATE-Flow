from .resource import BaseAPI
from ..entity.types import ResourceOperation


class FederatedAPI(BaseAPI):
    def create_job(self, job_id, roles, job_info):
        return self.job_command(job_id=job_id, roles=roles, command="create", command_body=job_info, parallel=False)

    def update_parameter(self, job_id, roles, updated_parameters):
        return self.job_command(job_id=job_id, roles=roles, command="parameter/update", command_body=updated_parameters,
                                parallel=False)

    def resource_for_job(self, job_id, roles, operation_type: ResourceOperation):
        return self.job_command(job_id=job_id, roles=roles, command=f"resource/{operation_type.value}")

    def check_component(self, job_id, roles, check_type):
        status_code, response = self.job_command(job_id=job_id, roles=roles, command=f"component/{check_type}/check")
        return status_code, response

    def dependence_for_job(self, job_id, roles):
        return self.job_command(job_id=job_id, roles=roles, command=f"dependence/check")

    def connect(self, job_id, roles, command_body):
        return self.job_command(job_id=job_id, roles=roles, command="align", command_body=command_body)

    def align_args(self, job_id, roles, command_body):
        return self.job_command(job_id=job_id, roles=roles, command="align", command_body=command_body)

    def start_job(self, job_id, roles, command_body):
        return self.job_command(job_id=job_id, roles=roles, command="start", command_body=command_body)

    def sync_job_status(self, job_id, roles, status, command_body=None):
        return self.job_command(job_id=job_id, roles=roles, command=f"status/{status}", command_body=command_body)

    def sync_job(self, job_id, roles, command_body=None):
        return self.job_command(job_id=job_id, roles=roles, command="update", command_body=command_body)

    def save_pipelined_model(self, job_id, roles):
        return self.job_command(job_id=job_id, roles=roles, command="model")

    def stop_job(self, job_id, roles, stop_status):
        return self.job_command(job_id=job_id, roles=roles, command="stop/{}".format(stop_status))

    def clean_job(self, job_id, roles, command_body=None):
        return self.job_command(job_id=job_id, roles=roles, command="clean", command_body=command_body)

    def create_task(self, tasks, command_body=None):
        return self.task_command(tasks=tasks, command="create", command_body=command_body)

    def start_task(self, tasks):
        return self.task_command(tasks=tasks, command="start")

    def collect_task(self, tasks):
        return self.task_command(tasks=tasks, command="collect")

    def sync_task_status(self, tasks, status):
        return self.task_command(tasks=tasks, command=f"status/{status}")

    def stop_task(self, tasks, stop_status, command_body=None):
        return self.task_command(tasks=tasks, command="stop/{}".format(stop_status), command_body=command_body)

    def clean_task(self, tasks, content_type):
        return self.task_command(tasks=tasks, command="clean/{}".format(content_type))
