from fate_flow.adapter.bfia import BfiaRuntimeConfig


class BfiaFederatedScheduler:
    # job
    @classmethod
    def create_job(cls, node_list, command_body):
        return BfiaRuntimeConfig.SCHEDULE_CLIENT.federated.create_job(
            node_list, command_body=command_body
        )

    @classmethod
    def start_job(cls, node_list, job_id):
        command_body = {
            "job_id": job_id
        }
        return BfiaRuntimeConfig.SCHEDULE_CLIENT.federated.start_job(
            node_list, command_body=command_body
        )

    @classmethod
    def stop_job(cls, node_list, command_body):
        return BfiaRuntimeConfig.SCHEDULE_CLIENT.federated.stop_job(
            node_list, command_body=command_body
        )

    @classmethod
    def poll_task_all(cls, node_list, task_id):
        command_body = {
            "task_id": task_id,
            "role": ""
        }
        return BfiaRuntimeConfig.SCHEDULE_CLIENT.federated.poll_task(node_list, command_body=command_body)

    @classmethod
    def start_task(cls, node_list, job_id, task_id, task_name):
        command_body = {
            "task_id": task_id,
            "task_name": task_name,
            "job_id": job_id
        }
        return BfiaRuntimeConfig.SCHEDULE_CLIENT.federated.start_task(node_list, command_body=command_body)

    # scheduler
    @classmethod
    def request_create_job(cls, party_id, command_body):
        return BfiaRuntimeConfig.SCHEDULE_CLIENT.scheduler.create_job(party_id, command_body)

    @classmethod
    def request_audit_confirm(cls, party_id, command_body):
        return BfiaRuntimeConfig.SCHEDULE_CLIENT.scheduler.audit_confirm(party_id, command_body)

    @classmethod
    def request_stop_job(cls, party_id, job_id):
        command_body = {
            "job_id": job_id
        }
        return BfiaRuntimeConfig.SCHEDULE_CLIENT.scheduler.stop_job(party_id, command_body)

    @classmethod
    def request_report_task(cls, party_id, command_body):
        return BfiaRuntimeConfig.SCHEDULE_CLIENT.scheduler.report_task(party_id, command_body)
