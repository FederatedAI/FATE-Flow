import abc
from abc import ABCMeta
from os import path

import traceback
import yaml
import json
import docker

from kubernetes import client, config, stream


class ManagerABC(metaclass=ABCMeta):
    @abc.abstractmethod
    def register_images(self):
        """
        服务启动时，初始化操作：注册环境中已有的镜像及算法组件、版本等信息，供调度层调度操作
        """
        ...

    @abc.abstractmethod
    def load_images(self, images_name, *args, **kwargs):
        """
        系统启动后，通过镜像名注册算法镜像(算法组件、版本等信息), 类似provider注册接口
        """

    @abc.abstractmethod
    def remove_images(self, url, *args, **kwargs):
        """
        系统启动后，卸载在系统上注册的算法镜像
        """

    @abc.abstractmethod
    def run_task(self, *args, **kwargs):
        """
        启动容器并使用容器命令启动任务
        任务结束清理容器
        """

    @abc.abstractmethod
    def stop_task(self, *args, **kwargs):
        """
        直接stop容器？资源相关释放问题(如eggroll的session清理)
        """

    @abc.abstractmethod
    def check_container(self, *args, **kwargs):
        """
        考虑：容器异常退出情况的资源释放
        """
        ...


class DockerManager(ManagerABC):
    def __init__(self):
        self.client = self._client()

    @staticmethod
    def _client():
        return docker.from_env()

    @property
    def container_names(self):
        return [cont.name for cont in self.client.containers.list()]

    @property
    def all_images(self, *args, **kwargs):
        return self.client.images.list()

    def register_images(self):
        for images in self.all_images:
            # todo: 注册镜像
            pass

    def load_images(self, image_name, **kwargs):
        image = self.client.images.get(image_name)
        # todo: 注册镜像

    def remove_images(self, image_name, **kwargs):
        image = self.client.images.get(image_name)
        image.remove(force=True)
        # todo: 注销镜像

    def run_task(self, image_name, container_name, cmd, environment):
        # 容器即用即销毁： 启动容器并运行task
        container = self.run_container(image_name, container_name)
        exec_out = container.exec_run(cmd=cmd, stream=False, workdir="/data/projects/fate", environment=environment)

    def stop_task(self, container_name):
        # session 清理
        self.stop_container(container_name)
        self.delete_container(container_name)

    def check_container(self, container_name):
        container = self.get_container(name=container_name)
        return container.status

    def get_container(self, name):
        return self.client.containers.get(name)

    def run_container(self, image_name, container_name, **kwargs):
        volumes = ["/data/logs:/data/projects/fate/fateflow/logs",
                   "/data/jobs:/data/projects/fate/fateflow/jobs",
                   ]
        return self.client.containers.run(image=image_name, name=container_name, detach=True, volumes=volumes)

    def stop_container(self, name):
        return self.get_container(name).stop()

    def delete_container(self, name):
        cont = self.get_container(name)
        return self.client.api.remove_container(cont.id)


class K8sManager(ManagerABC):

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

    def check_container(self):
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


