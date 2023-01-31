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


class K8sManager:
    image = WORKER.get('k8s', {}).get('image', '')

    def __init__(self):
        config.load_incluster_config()
        self.job_template = yaml.safe_load(
            (Path(__file__).parent / 'k8s_template.yaml').read_text('utf-8')
        )

    @property
    def namespace(self):
        # In below file, the pod can read its K8s namespace
        with open("/var/run/secrets/kubernetes.io/serviceaccount/namespace") as f:
            namespace = f.readline()
        return namespace

    def populate_yaml_template(self, name, command, environment):
        job_conf = copy.deepcopy(self.job_template)
        metadata = job_conf['metadata']
        container_spec = job_conf['spec']['template']['spec']['containers'][0]
        metadata['name'] = name
        metadata['namespace'] = self.namespace
        container_spec['name'] = name
        container_spec['image'] = self.image
        container_spec['command'] = command
        container_spec['env'] = [{'name': k, 'value': v} for k, v in environment.items()]
        return job_conf

    def start(self, name, command, environment, volumes):
        job_conf = self.populate_yaml_template(name, command, environment)
        client.BatchV1Api().create_namespaced_job(self.namespace, job_conf)

    def stop(self, name):
        body = client.V1DeleteOptions(propagation_policy='Background')
        client.BatchV1Api().delete_namespaced_job(name, self.namespace, body=body)

    def is_running(self, name):
        res = client.BatchV1Api().read_namespaced_job_status(name, self.namespace)
        if not res:
            return False
        return not (res.status.succeeded or res.status.failed)
