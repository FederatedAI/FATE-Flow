from .resource import BaseAPI


class WorkerAPI(BaseAPI):

    def task_parameters(self, task_info):
        endpoint = '/party/{}/{}/{}/{}/{}/{}/report'.format(
            task_info["job_id"],
            task_info["component_name"],
            task_info["task_id"],
            task_info["task_version"],
            task_info["role"],
            task_info["party_id"]
        )
        return self.client.post(endpoint=endpoint, json=task_info)

    def report_task(self, task_info):
        endpoint = '/party/{}/{}/{}/{}/{}/{}/report'.format(
            task_info["job_id"],
            task_info["component_name"],
            task_info["task_id"],
            task_info["task_version"],
            task_info["role"],
            task_info["party_id"]
        )
        return self.client.post(endpoint=endpoint, json=task_info)

    def output_metric(self, content):
        return self.client.post(endpoint="/worker/metric/write", json=content)

    def write_model(self, content):
        return self.client.post(endpoint="/worker/model/write", json=content)
