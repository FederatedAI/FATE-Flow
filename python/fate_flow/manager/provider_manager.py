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
#
import os
import subprocess
import sys

from fate_arch.common import file_utils
from fate_arch.common.versions import get_versions
from fate_flow.entity.component_provider import ComponentProvider
from fate_flow.worker.provider_registrar import ProviderRegistrar
from fate_flow.settings import stat_logger
from fate_flow.utils import process_utils, job_utils, base_utils
from fate_flow.db.component_registry import ComponentRegistry


class ProviderManager:
    @classmethod
    def register_default_providers(cls):
        code = cls.register_fate_flow_component_provider()
        if code != 0:
            raise Exception(f"register fate flow tools component failed")
        code = cls.register_default_fate_algorithm_component_provider()
        if code != 0:
            raise Exception(f"register default fate algorithm component failed")

    @classmethod
    def register_fate_flow_component_provider(cls):
        path = file_utils.get_python_base_directory("fate_flow")
        provider = ComponentProvider(name="fate_flow_tools", version=get_versions()["FATEFlow"], path=path, class_path=ComponentRegistry.get_default_class_path())
        return cls.start_registrar_process(provider)

    @classmethod
    def register_default_fate_algorithm_component_provider(cls):
        path = ["component_plugins",
                "fate",
                "python",
                "federatedml"]
        path = file_utils.get_python_base_directory(*path)
        provider = ComponentProvider(name="fate_algorithm", version=get_versions()["FATE"], path=path, class_path=ComponentRegistry.get_default_class_path())
        return cls.start_registrar_process(provider)

    @classmethod
    def start_registrar_process(cls, provider: ComponentProvider):
        stat_logger.info('try to start component registry initializer subprocess')
        worker_type = "provider_registrar"
        worker_id = base_utils.new_unique_id()
        message = f'{worker_type} {worker_id} subprocess'

        config_dir = job_utils.get_worker_directory(worker_type, worker_id)
        log_dir = job_utils.get_worker_log_directory(worker_type, worker_id)
        os.makedirs(config_dir, exist_ok=True)
        config_path = os.path.join(config_dir, f"config.json")
        config_data = {
            "provider": provider.to_dict()
        }
        file_utils.dump_json_conf(config_data, config_path)

        process_cmd = [
            sys.executable,
            sys.modules[ProviderRegistrar.__module__].__file__,
            '-c', config_path,
        ]

        p = process_utils.run_subprocess(job_id=None, config_dir=config_dir, process_cmd=process_cmd, extra_env=provider.env,
                                         log_dir=log_dir, cwd_dir=config_dir)
        stat_logger.info(f'{message} pid {p.pid} start')
        try:
            p.wait(timeout=5)
            return p.returncode
        except subprocess.TimeoutExpired as e:
            err = f"{message} pid {p.pid} run timeout"
            stat_logger.exception(err, e)
            raise Exception(err)
        finally:
            try:
                p.kill()
                p.poll()
            except Exception as e:
                stat_logger.exception(e)

    @classmethod
    def get_provider_object(cls, provider_info):
        name, version = provider_info["name"], provider_info["version"]
        path = ComponentRegistry.get_providers().get(name, {}).get(version, {}).get("path", [])
        class_path = ComponentRegistry.get_providers().get(name, {}).get(version, {}).get("class_path", None)
        if class_path is None:
            class_path = ComponentRegistry.REGISTRY["default_settings"]["class_path"]
        return ComponentProvider(name=name, version=version, path=path, class_path=class_path)

    @classmethod
    def get_job_provider_group(cls, dsl_parser, components: list = None):
        providers_info = dsl_parser.get_job_providers(provider_detail=ComponentRegistry.REGISTRY)
        # providers format: {'upload_0': {'module': 'Upload', 'provider': {'name': 'fate_flow_tools', 'version': '1.7.0'}}}

        group = {}
        if components is not None:
            _providers_info = {}
            for component_name in components:
                _providers_info[component_name] = providers_info.get(component_name)
            providers_info = _providers_info
        for component_name, provider_info in providers_info.items():
            provider = cls.get_provider_object(provider_info["provider"])
            group_key = ":".join([provider.name, provider.version])
            if group_key not in group:
                group[group_key] = {
                    "provider": provider.to_dict(),
                    "components": [component_name]
                }
            else:
                group[group_key]["components"].append(component_name)
        return group

    @classmethod
    def get_component_provider(cls, dsl_parser, component_name):
        providers = dsl_parser.get_job_providers(provider_detail=ComponentRegistry.REGISTRY)
        return cls.get_provider_object(providers[component_name]["provider"])

    @classmethod
    def get_component_parameters(cls, dsl_parser, component_name, role, party_id, provider: ComponentProvider = None):
        if not provider:
            provider = cls.get_component_provider(dsl_parser=dsl_parser,
                                                  component_name=component_name)
        component_parameters_on_party = dsl_parser.parse_component_parameters(component_name,
                                                                              ComponentRegistry.REGISTRY,
                                                                              provider.name,
                                                                              provider.version,
                                                                              local_role=role,
                                                                              local_party_id=party_id)
        return component_parameters_on_party

    @classmethod
    def get_component_run_info(cls, dsl_parser, component_name, role, party_id):
        provider = cls.get_component_provider(dsl_parser, component_name)
        parameters = cls.get_component_parameters(dsl_parser, component_name, role, party_id, provider)
        return provider, parameters
