import threading

from ..api import APIClient


class BaseAPI:
    def __init__(self, client: APIClient):
        self.client = client

    def command(self, job_id, src_role, src_party_id, dest_role, dest_party_id, endpoint, body,
                federated_mode, federated_response):
        try:
            response = self.client.remote(job_id=job_id,
                                          method='POST',
                                          endpoint=endpoint,
                                          src_role=src_role,
                                          src_party_id=src_party_id,
                                          dest_party_id=dest_party_id,
                                          json_body=body if body else {},
                                          federated_mode=federated_mode)
        except Exception as e:
            response = {
                "retcode": 1,
                "retmsg": "Federated schedule error, {}".format(e)
            }
        return response

    @classmethod
    def job_command(cls, job, command, command_body=None, dest_only_initiator=False, specific_dest=None, parallel=False):
        federated_response = {}
        job_parameters = job.f_runtime_conf_on_party["job_parameters"]
        if dest_only_initiator:
            dest_partis = [(job.f_initiator_role, [job.f_initiator_party_id])]
            api_type = "initiator"
        elif specific_dest:
            dest_partis = specific_dest.items()
            api_type = "party"
        else:
            dest_partis = job.f_roles.items()
            api_type = "party"
        threads = []
        for dest_role, dest_party_ids in dest_partis:
            federated_response[dest_role] = {}
            for dest_party_id in dest_party_ids:
                endpoint = f"/{api_type}/{job.f_job_id}/{dest_role}/{dest_party_id}/{command}"
                args = (job.f_job_id, job.f_role, job.f_party_id, dest_role, dest_party_id, endpoint, command_body, job_parameters["federated_mode"], federated_response)
                if parallel:
                    t = threading.Thread(target=cls.command, args=args)
                    threads.append(t)
                    t.start()
                else:
                    cls.command(*args)
        for thread in threads:
            thread.join()
        return cls.return_federated_response(federated_response=federated_response)

    @classmethod
    def task_command(cls, job: Job, task: Task, command, command_body=None, parallel=False, need_user=False):
        msg = f"execute federated task {task.f_component_name} command({command})"
        federated_response = {}
        job_parameters = job.f_runtime_conf_on_party["job_parameters"]
        threads = []
        for task in tasks:
            dest_role, dest_party_id = task.f_role, task.f_party_id
            federated_response[dest_role] = federated_response.get(dest_role, {})
            endpoint = f"/party/{task.f_job_id}/{task.f_component_name}/{task.f_task_id}/{task.f_task_version}/{dest_role}/{dest_party_id}/{command}"
            if need_user:
                command_body["user_id"] = job.f_user.get(dest_role, {}).get(str(dest_party_id), "")
            args = (job.f_job_id, job.f_role, job.f_party_id, dest_role, dest_party_id, endpoint, command_body, job_parameters["federated_mode"], federated_response)
            if parallel:
                t = threading.Thread(target=cls.command, args=args)
                threads.append(t)
                t.start()
            else:
                cls.command(*args)
        for thread in threads:
            thread.join()
        status_code, response = cls.return_federated_response(federated_response=federated_response)
        return status_code, response

    @classmethod
    def scheduler_command(cls):
        pass

    @classmethod
    def return_federated_response(cls, federated_response):
        retcode_set = set()
        for dest_role in federated_response.keys():
            for party_id in federated_response[dest_role].keys():
                retcode_set.add(federated_response[dest_role][party_id]["retcode"])
        if len(retcode_set) == 1 and RetCode.SUCCESS in retcode_set:
            federated_scheduling_status_code = FederatedSchedulingStatusCode.SUCCESS
        elif RetCode.EXCEPTION_ERROR in retcode_set:
            federated_scheduling_status_code = FederatedSchedulingStatusCode.ERROR
        elif RetCode.NOT_EFFECTIVE in retcode_set:
            federated_scheduling_status_code = FederatedSchedulingStatusCode.NOT_EFFECTIVE
        elif RetCode.SUCCESS in retcode_set:
            federated_scheduling_status_code = FederatedSchedulingStatusCode.PARTIAL
        else:
            federated_scheduling_status_code = FederatedSchedulingStatusCode.FAILED
        return federated_scheduling_status_code, federated_response
