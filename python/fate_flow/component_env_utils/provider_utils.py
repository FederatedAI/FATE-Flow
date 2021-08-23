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
import importlib
import pathlib

from fate_arch.common import file_utils
from fate_flow.entity.component_provider import ComponentProvider
from fate_flow.db.runtime_config import RuntimeConfig
from fate_flow.settings import stat_logger, FATE_FLOW_DIRECTORY
import sys
from fate_flow.operation.component_registry_initializer import ComponentRegistryInitializer
from fate_flow.utils import process_utils
import subprocess


def component_provider(provider_info):
    name, version = provider_info["name"], provider_info["version"]
    path = RuntimeConfig.COMPONENT_REGISTRY["provider"].get(name, {}).get(version, {}).get("path", [])
    return ComponentProvider(name=name, version=version, path=path)


def get_job_provider_group(dsl_parser, component_name=None):
    providers = dsl_parser.get_job_providers(provider_detail=RuntimeConfig.COMPONENT_REGISTRY)
    # providers format: {'upload_0': {'module': 'Upload', 'provider': {'name': 'fate_flow_tools', 'version': '1.7.0'}}}

    group = {}
    if component_name is not None:
        providers = {component_name: providers.get(component_name)}
    for component_name, provider_info in providers.items():
        provider = component_provider(provider_info["provider"])
        group_key = ":".join([provider.name, provider.version])
        if group_key not in group:
            group[group_key] = {
                "provider": provider.to_json(),
                "components": [component_name]
            }
        else:
            group[group_key]["components"].append(component_name)
    return group


def get_component_provider(dsl_parser, component_name):
    providers = dsl_parser.get_job_providers(provider_detail=RuntimeConfig.COMPONENT_REGISTRY)
    return component_provider(providers[component_name]["provider"])


def get_component_parameters(dsl_parser, component_name, role, party_id, provider: ComponentProvider = None):
    if not provider:
        provider = get_component_provider(dsl_parser=dsl_parser,
                                          component_name=component_name)
    component_parameters_on_party = dsl_parser.parse_component_parameters(component_name,
                                                                          RuntimeConfig.COMPONENT_REGISTRY,
                                                                          provider.name,
                                                                          provider.version,
                                                                          local_role=role,
                                                                          local_party_id=party_id)
    return component_parameters_on_party


def get_component_run_info(dsl_parser, component_name, role, party_id):
    provider = get_component_provider(dsl_parser, component_name)
    parameters = get_component_parameters(dsl_parser, component_name, role, party_id, provider)
    return provider, parameters


def get_provider_interface(provider: ComponentProvider):
    obj = get_component_class(provider, "interface")
    setattr(obj, "provider_name", provider.name)
    setattr(obj, "provider_version", provider.version)
    return obj


def get_component_model(provider: ComponentProvider):
    class_path = get_component_class_path(provider, "model")
    return pathlib.Path(file_utils.get_python_base_directory(*class_path.split("."))), class_path


def get_component_class(provider: ComponentProvider, class_name):
    class_path = get_component_class_path(provider, class_name).split(".")
    return getattr(importlib.import_module(".".join(class_path[:-1])), class_path[-1])


def get_component_class_path(provider: ComponentProvider, class_name):
    class_abspath = RuntimeConfig.COMPONENT_REGISTRY["provider"].get(provider.name, {}).get(provider.version, {}).get("class_path", {}).get(class_name, None)
    if not class_abspath:
        class_abspath = RuntimeConfig.COMPONENT_REGISTRY["default_settings"]["class_path"][class_name]
    return f"{provider.path[-1]}.{class_abspath}"


def init_component_registry():
    stat_logger.info('try to start component registry initializer subprocess')
    initialize_dir = FATE_FLOW_DIRECTORY

    process_cmd = [
        sys.executable,
        sys.modules[ComponentRegistryInitializer.__module__].__file__,
    ]
    log_dir = FATE_FLOW_DIRECTORY
    default_component_provider_paths = [
        file_utils.get_python_base_directory(*"component_plugins.fate.python".split("."))
    ]
    env = {
        "PYTHONPATH": ":".join(default_component_provider_paths)
    }
    p = process_utils.run_subprocess(job_id=None, config_dir=initialize_dir, process_cmd=process_cmd, extra_env=env, log_dir=log_dir, cwd_dir=initialize_dir)
    stat_logger.info('component registry initializer subprocess pid {} is ready'.format(p.pid))
    try:
        p.communicate(timeout=5)
        # return code always 0 because of server wait_child_process, can not use to check
        #todo: check
    except subprocess.TimeoutExpired as e:
        err = f"component registry initializer subprocess pid {p.pid} run timeout"
        stat_logger.exception(err, e)
        p.kill()
        raise Exception(err)
