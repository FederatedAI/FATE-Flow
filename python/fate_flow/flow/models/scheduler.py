from .resource import BaseAPI


class SchedulerAPI(BaseAPI):
    def create_job(self, content):
        return self.scheduler_command()

    def start_job(self, content):
        return self.scheduler_command()

    def stop_job(self, content):
        return self.scheduler_command()

    def rerun_job(self, content):
        return self.scheduler_command()
