from os import path

import traceback
import yaml
import json
import docker

from kubernetes import client, config, stream


class BaseManager:
    def run_task(self, *args, **kwargs):
        pass

    def stop_task(self, *args, **kwargs):
        pass

    def check_task(self, *args, **kwargs):
        pass

    def component_status(self, *args, **kwargs):
        pass

    def component_registry(self, *args, **kwargs):
        pass

    def component_revoke(self, *args, **kwargs):
        pass


class DockerManager(BaseManager):
    @property
    def client(self):
        docker.DockerClient()
        return docker.from_env()

    @property
    def container_names(self):
        return [cont.name for cont in self.client.containers.list()]

    @property
    def all_images(self):
        return self.client.images.list()

    def get_container(self, name):
        return self.client.containers.get(name)

    def run_container(self, image, name, **kwargs):
        volumes = ["/data/logs:/data/projects/fate/fateflow/logs",
                   "/data/jobs:/data/projects/fate/fateflow/jobs",
                   ]
        return self.client.containers.run(image=image, name=name, detach=True, volumes=volumes)

    def get_status(self, name):
        container = self.get_container(name=name)
        return container.status

    def exec_run(self, cmd, name, environment=None):
        if not environment:
            environment = {"PATH": "/data/projects/fate/env/python36/venv/bin/python",
                           'PYTHONPATH': "/data/projects/fate/fateflow/python:/data/projects/fate/fate/python"}
        container = self.get_container(name=name)
        exec_out = container.exec_run(cmd=cmd, stream=False, workdir="/data/projects/fate", environment=environment)
        try:
            return json.loads(exec_out.output)
        except:
            return bytes.decode(exec_out.output)

    def stop_container(self, name):
        return self.get_container(name).stop()

    def delete_container(self, name):
        cont = self.get_container(name)
        return self.client.api.remove_container(cont.id)

    def run_task(self, cmd, name):
        return self.exec_run(cmd, name)

    def stop_task(self, cmd, name):
        return self.exec_run(cmd, name)

    def component_status(self, name):
        return self.get_status(name=name)

    def component_registry(self, image, name):
        pass

    def component_revoke(self, *args, **kwargs):
        pass

    def check_task(self, *args, **kwargs):
        pass


class K8sManager(BaseManager):

    # This manager is for managing the algorithm container under k8s env,
    # especially when FATE is deployed by KubeFATE.

    def __init__(self, image):
        self.core_api = client.CoreV1Api()
        self.app_api = client.AppsV1Api()
        self.namespace = K8sUtils.get_namespace()
        self._load_yaml_file("yaml-files/algorithm.yaml", image)
        self.sts_name = self.sts_conf.get("metadata", {}).get("name")
        self.pod_name = "%s-0" % self.sts_name
        if not self.sts_name:
            print("failed to read the sts name from the sts yaml file")

    def _load_yaml_file(self, file_path: str, image: str):
        with open(path.join(path.dirname(__file__), file_path)) as f:
            self.sts_conf = yaml.safe_load(f)
        self.sts_conf['spec']['template']['spec']['containers'][0]['image'] = image

    def create_sts(self) -> bool:
        try:
            resp = self.app_api.create_namespaced_stateful_set(
                namespace=self.namespace, body=self.sts_conf)
            return True
        except:
            traceback.print_exc()
            return False

    def is_sts_exist(self) -> bool:
        sts_list = [sts.metadata.name for sts in
                    self.app_api.list_namespaced_stateful_set(self.namespace).items]
        return True if self.sts_name in sts_list else False

    def describe_sts(self) -> client.V1StatefulSet:
        resp = self.app_api.read_namespaced_stateful_set_status(
            namespace=self.namespace, name=self.sts_name)
        return resp

    def is_pod_ready(self) -> bool:
        if not self.is_sts_exist():
            return False
        return self.describe_sts().status.ready_replicas > 0

    def destroy_sts(self) -> bool:
        try:
            resp = self.app_api.delete_namespaced_stateful_set(
                name=self.sts_name,
                namespace=self.namespace,
            )
            if resp.status.lower() == K8sUtils.SUCCESS:
                return True
            return False
        except:
            traceback.print_exc()
            return False

    def exec_run(self, commands: list) -> str:
        # Calling exec and waiting for response
        try:
            output = stream.stream(
                self.core_api.connect_get_namespaced_pod_exec,
                name=self.pod_name,
                namespace=self.namespace,
                command=commands,
                stderr=True, stdin=False,
                stdout=True, tty=False)
            print("Response: " + output)
        except:
            traceback.print_exc()
            output = None
        return output

    def run_task(self, cmd, name):
        return self.exec_run(cmd, name)

    def stop_task(self, cmd, name):
        return self.exec_run(cmd, name)

    def component_status(self):
        return self.is_pod_ready()

    def component_registry(self, image, name):
        pass

    def component_revoke(self, *args, **kwargs):
        pass

    def check_task(self, *args, **kwargs):
        pass


class K8sUtils:
    SUCCESS = "success"

    @classmethod
    def load_in_cluster_config(cls) -> None:
        config.load_incluster_config()

    @classmethod
    def get_namespace(cls) -> str:
        # In below file, the pod can read it is in which K8s namespace
        with open("/var/run/secrets/kubernetes.io/serviceaccount/namespace") as f:
            namespace = f.readline()
        return namespace


'''
# Usage:
if __name__ == '__main__':
    K8sUtils.load_in_cluster_config()
    # Control using which algorithm here
    k8s_manager = K8sManager(image="federatedai/algorithm:v2.0")
    k8s_manager.create_sts()
    exec_command = [
        '/bin/sh',
        '-c',
        'mkdir /data/projects/fate/fateflow/logs/hello'
    ]
    k8s_manager.exec_run(exec_command)
    res = k8s_manager.is_sts_exist()
    res = k8s_manager.is_pod_ready()
    k8s_manager.destroy_sts()
'''

