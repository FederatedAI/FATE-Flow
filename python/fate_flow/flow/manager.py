import json

import docker


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
