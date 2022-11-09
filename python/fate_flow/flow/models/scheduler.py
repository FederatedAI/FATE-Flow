from .resource import BaseAPI


class SchedulerAPI(BaseAPI):
    def create_job(self, party_id, command_body):
        return self.scheduler_command(command="job/create",
                                      party_id=party_id,
                                      command_body=command_body
                                      )

    def stop_job(self, party_id, command_body):
        return self.scheduler_command(command="job/stop",
                                      party_id=party_id,
                                      command_body=command_body
                                      )

    def rerun_job(self, party_id, command_body):
        return self.scheduler_command(command="job/rerun",
                                      party_id=party_id,
                                      command_body=command_body
                                      )

    def report_task(self, party_id, command_body):
        return self.scheduler_command(command="task/report",
                                      party_id=party_id,
                                      command_body=command_body
                                      )
