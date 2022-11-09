import threading

from ..api import APIClient
from ..entity.run_status import FederatedSchedulingStatusCode
from ..entity.types import RetCode, Task


class BaseAPI:
    def __init__(self, client: APIClient):
        self.client = client

    def federated_command(self, job_id, src_role, src_party_id, dest_role, dest_party_id, endpoint, body,
                          federated_response, federated_mode=None, method='POST', only_scheduler=False):
        try:
            response = self.client.remote(job_id=job_id,
                                          method=method,
                                          endpoint=endpoint,
                                          src_role=src_role,
                                          src_party_id=src_party_id,
                                          dest_party_id=dest_party_id,
                                          json_body=body if body else {},
                                          federated_mode=federated_mode)
            if only_scheduler:
                return response
        except Exception as e:
            response = {
                "retcode": RetCode.FEDERATED_ERROR,
                "retmsg": "Federated schedule error, {}".format(e)
            }
        federated_response[dest_role][dest_party_id] = response

    def job_command(self, job_id, roles, command, command_body=None, parallel=False):
        federated_response = {}
        api_type = "party"
        dest_partis = roles.items()
        threads = []
        for dest_role, dest_party_ids in dest_partis:
            federated_response[dest_role] = {}
            for dest_party_id in dest_party_ids:
                endpoint = f"/{api_type}/{job_id}/{dest_role}/{dest_party_id}/{command}"
                args = (job_id, "", "", dest_role, dest_party_id, endpoint, command_body, federated_response)
                if parallel:
                    t = threading.Thread(target=self.federated_command, args=args)
                    threads.append(t)
                    t.start()
                else:
                    self.federated_command(*args)
        for thread in threads:
            thread.join()
        return self.return_federated_response(federated_response=federated_response)

    def task_command(self, tasks, command, command_body=None, parallel=False):
        federated_response = {}
        threads = []
        for task in tasks:
            dest_role, dest_party_id = task["role"], task["party_id"]
            federated_response[dest_role] = federated_response.get(dest_role, {})
            endpoint = f"/party/{task['job_id']}/{task['component_name']}/{task['task_id']}/{task['task_version']}/{dest_role}/{dest_party_id}/{command}"
            args = (task['job_id'], task['role'], task['party_id'], dest_role, dest_party_id, endpoint, command_body, federated_response)
            if parallel:
                t = threading.Thread(target=self.federated_command, args=args)
                threads.append(t)
                t.start()
            else:
                self.federated_command(*args)
        for thread in threads:
            thread.join()
        status_code, response = self.return_federated_response(federated_response=federated_response)
        return status_code, response

    def scheduler_command(self, command, party_id, command_body=None, method='POST'):
        try:
            federated_response = {}
            endpoint = f"/scheduler/{command}"
            response = self.federated_command(job_id="",
                                              method=method,
                                              endpoint=endpoint,
                                              src_role="",
                                              src_party_id="",
                                              dest_role="",
                                              dest_party_id=party_id,
                                              body=command_body if command_body else {},
                                              federated_response=federated_response,
                                              only_scheduler=True
                                              )
        except Exception as e:
            response = {
                "retcode": RetCode.FEDERATED_ERROR,
                "retmsg": "Federated schedule error, {}".format(e)
            }
        return response

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
