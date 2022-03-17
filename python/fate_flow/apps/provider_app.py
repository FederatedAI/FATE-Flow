#
#  Copyright 2021 The FATE Authors. All Rights Reserved.
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
import copy
from pathlib import Path

from flask import request

from fate_flow.db.component_registry import ComponentRegistry
from fate_flow.entity import ComponentProvider, RetCode
from fate_flow.entity.types import WorkerName
from fate_flow.manager.worker_manager import WorkerManager
from fate_flow.utils.api_utils import error_response, get_json_result
from fate_flow.utils.detect_utils import validate_request


@manager.route('/register', methods=['POST'])
@validate_request("name", "version", "path")
def register():
    info = request.json or request.form.to_dict()
    if not Path(info["path"]).is_dir():
        return error_response(400, "invalid path")

    provider = ComponentProvider(name=info["name"],
                                 version=info["version"],
                                 path=info["path"],
                                 class_path=info.get("class_path", ComponentRegistry.get_default_class_path()))
    code, std = WorkerManager.start_general_worker(worker_name=WorkerName.PROVIDER_REGISTRAR, provider=provider)
    if code == 0:
        ComponentRegistry.load()
        if ComponentRegistry.get_providers().get(provider.name, {}).get(provider.version, None) is None:
            return get_json_result(retcode=RetCode.OPERATING_ERROR, retmsg=f"not load into memory")
        else:
            return get_json_result()
    else:
        return get_json_result(retcode=RetCode.OPERATING_ERROR, retmsg=f"register failed:\n{std}")


@manager.route('/registry/get', methods=['POST'])
def get_registry():
    return get_json_result(data=ComponentRegistry.REGISTRY)


@manager.route('/get', methods=['POST'])
def get_providers():
    providers = ComponentRegistry.get_providers()
    result = {}
    for name, group_detail in providers.items():
        result[name] = {}
        for version, detail in group_detail.items():
            result[name][version] = copy.deepcopy(detail)
            if "components" in detail:
                result[name][version]["components"] = set([c.lower() for c in detail["components"].keys()])
    return get_json_result(data=result)


@manager.route('/<provider_name>/get', methods=['POST'])
def get_provider(provider_name):
    return get_json_result(data=ComponentRegistry.get_providers().get(provider_name))
