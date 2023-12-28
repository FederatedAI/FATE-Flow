#
#  Copyright 2019 The FATE Authors. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
import docker

from fate_flow.runtime.component_provider import ComponentProvider


class DockerManager:
    def __init__(self, provider: ComponentProvider):
        self.provider = provider
        self.client = docker.DockerClient(base_url=provider.metadata.base_url)

    def start(self, name, command, environment, auto_remove=False, detach=True, network_mode="host", volumes=None):
        if not volumes:
            volumes = {}
        self.client.containers.run(
            self.provider.metadata.image, command,
            auto_remove=auto_remove, detach=detach,
            environment=environment, name=name,
            network_mode=network_mode, volumes=volumes
        )

    def stop(self, name):
        try:
            container = self.client.containers.get(name)
        except docker.errors.NotFound:
            return
        return container.remove(force=True)

    def is_running(self, name):
        try:
            container = self.client.containers.get(name)
        except docker.errors.NotFound:
            return False
        return container.status == 'running'

    def exit_with_exception(self, name):
        try:
            container = self.client.containers.get(name)
        except docker.errors.NotFound:
            return False
        return int(container.attrs['State']['ExitCode']) != 0

    def get_labels(self):
        image = self.client.images.get(self.provider.metadata.image)
        return image.labels

    def get_env(self):
        image = self.client.images.get(self.provider.metadata.image)
        return image.attrs.get("Config").get("Env")
