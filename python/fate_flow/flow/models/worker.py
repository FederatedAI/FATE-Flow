from .resource import BaseAPI


class WorkerAPI(BaseAPI):

    def task_parameters(self, content):
        return self.client.post(endpoint="/worker/parameters/get", json=content)

    def report(self, content):
        return self.client.post(endpoint="/worker/report", json=content)

    def output_metric(self, content):
        return self.client.post(endpoint="/worker/metric/write", json=content)

    def write_model(self, content):
        return self.client.post(endpoint="/worker/model/write", json=content)
