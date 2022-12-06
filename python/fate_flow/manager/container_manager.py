import abc
from abc import ABCMeta
from os import path

import traceback
import yaml
import docker
import copy

from kubernetes import client, config


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

    SUCCESS = "success"

    # This manager is for managing the algorithm container under k8s env,
    # especially when FATE is deployed by KubeFATE.

    # One thing need to be noted:
    # If we want to call run_task by multi-threading, make sure that there
    # are no 2 tasks sharing the same name, because K8s cannot create 2 jobs
    # with the same name at the same time in the Cluster.

    def __init__(self):
        config.load_incluster_config()
        self.batch_api = client.BatchV1Api()
        self.namespace = self._get_namespace()
        self._load_yaml_template("yaml-files/algorithm.yaml")

    def _get_namespace(self) -> str:
        # In below file, the pod can read its K8s namespace
        with open("/var/run/secrets/kubernetes.io/serviceaccount/namespace") as f:
            namespace = f.readline()
        return namespace

    def _load_yaml_template(self, file_path: str):
        with open(path.join(path.dirname(__file__), file_path)) as f:
            self.job_template = yaml.safe_load(f)

    def _populate_yaml_template(self, job_name: str, image: str, cmds: [str]) -> dict:
        if not self.job_template:
            print("cannot populate an non-existing template")
        job_conf = copy.deepcopy(self.job_template)
        metadata = job_conf['metadata']
        container_spec = job_conf['spec']['template']['spec']['containers'][0]
        metadata['name'] = job_name
        metadata['namespace'] = self.namespace
        container_spec['name'] = job_name
        container_spec['image'] = image
        container_spec['command'].extend(cmds)
        return job_conf

    def create_job(self, job_name: str, image: str, cmds: [str]) -> bool:
        try:
            job_conf = self._populate_yaml_template(job_name, image, cmds)
            self.batch_api.create_namespaced_job(
                namespace=self.namespace, body=job_conf)
            return True
        except:
            traceback.print_exc()
            return False

    def get_job_status(self, job_name: str) -> str:
        res = self.batch_api.read_namespaced_job_status(job_name, self.namespace)
        status = res.status.succeeded
        # CHANGE ME: change the status string per need.
        if not status:
            return "RUNNING"
        elif status <= 0:
            return "FAILURE"
        return "SUCCEED"

    def destroy_job(self, job_name: str) -> bool:
        try:
            resp = self.batch_api.delete_namespaced_job(
                name=job_name,
                namespace=self.namespace,
            )
            if resp.status.lower() == K8sManager.SUCCESS:
                return True
            return False
        except:
            traceback.print_exc()
            return False

    def run_task(self, cmd, name, image) -> bool:
        return self.create_job(
            job_name=name, image=image, cmds=[cmd])

    def stop_task(self, name) -> bool:
        return self.destroy_job(job_name=name)

    def check_container(self, name) -> str:
        return self.get_job_status(job_name=name)

    def component_registry(self, image, name):
        pass

    def component_revoke(self, *args, **kwargs):
        pass

    def check_task(self, *args, **kwargs):
        pass
