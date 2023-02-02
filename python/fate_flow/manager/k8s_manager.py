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
import copy
from pathlib import Path

from kubernetes import client, config
from ruamel import yaml

from fate_flow.settings import WORKER
from fate_flow.utils.conf_utils import get_base_config
from fate_flow.utils.log import getLogger

LOGGER = getLogger("k8s-manager")


class K8sManager:
    image = WORKER.get('k8s', {}).get('image', '')
    namespace = WORKER.get('k8s', {}).get('namespace', '')
    def __init__(self):
        config.load_kube_config()
        self.job_template = yaml.safe_load(
            (Path(__file__).parent / 'k8s_template.yaml').read_text('utf-8')
        )
        self.job_conf_template = yaml.safe_load(
            (Path(__file__).parent / 'k8s_conf_template.yaml').read_text('utf-8')
        )

    def populate_yaml_template(self, name, command, environment):
        job = copy.deepcopy(self.job_template)
        metadata = job['metadata']
        container_spec = job['spec']['template']['spec']['containers'][0]
        metadata['name'] = self.convertname(name)
        metadata['namespace'] = self.namespace
        container_spec['name'] = self.convertname(name)
        container_spec['image'] = self.image
        container_spec['command'] = ["/data/projects/fate/env/python/venv/bin/python"]
        container_spec['args'] = command
        container_spec['env'] = [{'name': k, 'value': v} for k, v in environment.items()]
        volumes=job['spec']['template']['spec']['volumes'][0]
        volumes['configMap']['name']=self.convertname(name + "job-conf")
        return job
    def populate_conf_yaml_template(self, name, service_conf):
        job_conf = copy.deepcopy(self.job_conf_template)
        metadata = job_conf['metadata']
        metadata['name'] = self.convertname(name + "job-conf")
        metadata['namespace'] = self.namespace
        job_conf['data']['service_conf.yaml'] = service_conf
        return job_conf

    def start(self, name, command, environment):
        # LOGGER.debug(f"command: {type(command)}, {command}")
        job = self.populate_yaml_template(self.convertname(name), command, environment)
        service_conf=yaml.safe_dump(get_base_config(key=None), default_flow_style=False)
        job_conf = self.populate_conf_yaml_template(self.convertname(name), service_conf)
        LOGGER.debug(f"job: {job}")
        LOGGER.debug(f"job_conf: {job}")
        client.CoreV1Api().create_namespaced_config_map(self.namespace, job_conf)
        client.BatchV1Api().create_namespaced_job(self.namespace, job)

    def stop(self, name):
        LOGGER.debug(f"stop job {name}")
        body = client.V1DeleteOptions(propagation_policy='Background')
        client.BatchV1Api().delete_namespaced_job(self.convertname(name), self.namespace, body=body, async_req=True)
        client.CoreV1Api().delete_namespaced_config_map(self.convertname(name + "job-conf"),self.namespace, body=body, async_req=True)

    def is_running(self, name):
        res = client.BatchV1Api().read_namespaced_job_status(self.convertname(name), self.namespace)
        # LOGGER.debug(f"res: {res}")
        if not res:
            return False
        return not (res.status.succeeded or res.status.failed)
    
    # convertname: Ensure that name composes the RFC 1123 specification
    def convertname(self, name):
        return name.lower().replace('_','-')