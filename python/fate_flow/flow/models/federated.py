from .resource import BaseAPI


class FederatedAPI(BaseAPI):
    @classmethod
    def create_job(cls, job: Job):
        return cls.job_command(job=job, command="create", command_body=job.to_human_model_dict(), parallel=False)

    @classmethod
    def resource_for_job(cls, job, operation_type: ResourceOperation, specific_dest=None):
        return cls.job_command(job=job, command=f"resource/{operation_type.value}", specific_dest=specific_dest)

    @classmethod
    def start_job(cls, job, command_body=None):
        return cls.job_command(job=job, command="start", command_body=command_body)

    @classmethod
    def sync_job_status(cls, job):
        return cls.job_command(job=job, command=f"status/{job.f_status}", command_body=job.to_human_model_dict())

    @classmethod
    def stop_job(cls, job, stop_status):
        job.f_status = stop_status
        return cls.job_command(job=job, command="stop/{}".format(stop_status))

    @classmethod
    def rerun_job(cls, job, command_body):
        return cls.job_command(job=job, command="rerun", command_body=command_body, dest_only_initiator=True)

    @classmethod
    def clean_job(cls, job):
        return cls.job_command(job=job, command="clean", command_body=job.f_runtime_conf_on_party["role"].copy())

    @classmethod
    def create_task(cls, job, task):
        return cls.task_command(job=job, task=task, command="create", command_body=task.to_human_model_dict())

    @classmethod
    def start_task(cls, job, task):
        return cls.task_command(job=job, task=task, command="start", command_body={}, need_user=True)

    @classmethod
    def collect_task(cls, job, task):
        return cls.task_command(job=job, task=task, command="collect")

    @classmethod
    def sync_task_status(cls, job, task):
        return cls.task_command(job=job, task=task, command=f"status/{task.f_status}")

    @classmethod
    def stop_task(cls, job, task, stop_status, command_body=None):
        return cls.task_command(job=job, task=task, command="stop/{}".format(stop_status), command_body=command_body)

    @classmethod
    def clean_task(cls, job, task, content_type: TaskCleanResourceType):
        return cls.task_command(job=job, task=task, command="clean/{}".format(content_type.value))
