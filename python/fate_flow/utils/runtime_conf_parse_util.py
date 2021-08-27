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

import copy
from fate_arch import common
from fate_arch.abc import Components
from fate_flow.utils.dsl_exception import RoleParameterNotConsistencyError, ModuleNotExistError, \
    RoleParameterNotListError
from fate_flow.component_env_utils import provider_utils
from fate_flow.entity.component_provider import ComponentProvider
from fate_flow.db.runtime_config import RuntimeConfig


class RuntimeConfParserUtil(object):
    @classmethod
    def get_input_parameters(cls, submit_dict, components=None, conf_version=1):
        if conf_version == 1:
            return RuntimeConfParserV1.get_input_parameters(submit_dict)
        else:
            return RuntimeConfParserV2.get_input_parameters(submit_dict, components=components)

    @classmethod
    def get_job_parameters(cls, submit_dict, conf_version=1):
        if conf_version == 1:
            return RuntimeConfParserV1.get_job_parameters(submit_dict)
        else:
            return RuntimeConfParserV2.get_job_parameters(submit_dict)

    @staticmethod
    def merge_dict(dict1, dict2):
        merge_ret = {}
        key_set = dict1.keys() | dict2.keys()
        for key in key_set:
            if key in dict1 and key in dict2:
                val1 = dict1.get(key)
                val2 = dict2.get(key)
                if isinstance(val1, dict):
                    merge_ret[key] = RuntimeConfParserUtil.merge_dict(val1, val2)
                else:
                    merge_ret[key] = val2
            elif key in dict1:
                merge_ret[key] = dict1.get(key)
            else:
                merge_ret[key] = dict2.get(key)

        return merge_ret

    @staticmethod
    def generate_predict_conf_template(predict_dsl, train_conf, model_id, model_version, conf_version=1):
        if conf_version == 1:
            return RuntimeConfParserV1.generate_predict_conf_template(predict_dsl, train_conf, model_id, model_version)
        else:
            return RuntimeConfParserV2.generate_predict_conf_template(predict_dsl, train_conf, model_id, model_version)

    @staticmethod
    def get_module_name(module, role, provider: Components):
        return provider.get(module, RuntimeConfig.get_provider_components(provider.provider_name, provider.provider_version)).get_run_obj_name(role)

    @staticmethod
    def get_component_parameters(
        provider,
        runtime_conf,
        module,
        alias,
        redundant_param_check,
        conf_version,
        local_role,
        local_party_id,
    ):
        provider_components = RuntimeConfig.get_provider_components(
            provider.provider_name, provider.provider_version
        )
        support_roles = provider.get(module, provider_components).get_supported_roles()
        if runtime_conf["role"] is not None:
            support_roles = [r for r in runtime_conf["role"] if r in support_roles]
        role_on_module = copy.deepcopy(runtime_conf["role"])
        for role in runtime_conf["role"]:
            if role not in support_roles:
                del role_on_module[role]

        if local_role not in role_on_module:
            return {}

        conf = dict()
        for key, value in runtime_conf.items():
            if key not in [
                "algorithm_parameters",
                "role_parameters",
                "component_parameters",
            ]:
                conf[key] = value

        conf["role"] = role_on_module
        conf["local"] = runtime_conf.get("local", {})
        conf["local"].update({"role": local_role, "party_id": local_party_id})
        conf["module"] = module
        conf["CodePath"] = provider.get(module, provider_components).get_run_obj_name(
            local_role
        )

        param_class = provider.get(module, provider_components).get_param_obj(alias)
        role_idx = role_on_module[local_role].index(local_party_id)

        # conf_version == 2
        if conf_version == 2:
            # update common parameters
            common_parameters = (
                runtime_conf.get("component_parameters", {}).get("common", {}).get(alias)
            )
            if common_parameters is not None:
                param_class = param_class.update(
                    common_parameters, not redundant_param_check
                )

            # update role parameters
            for role_id, role_id_parameters in (
                runtime_conf.get("component_parameters", {})
                .get("role", {})
                .get(local_role, {})
                .items()
            ):
                if role_id == "all" or str(role_idx) in role_id.split("|"):
                    parameters = role_id_parameters.get(alias, None)
                    if parameters is not None:
                        param_class.update(parameters, not redundant_param_check)

        elif conf_version == 1:
            # update common parameters
            common_parameters = runtime_conf.get("algorithm_parameters", {}).get(alias)
            if common_parameters is not None:
                param_class = param_class.update(
                    common_parameters, not redundant_param_check
                )

            # update role parameters
            parameters = (
                runtime_conf.get("role_parameters", {}).get(local_role, {}).get(alias, {})
            )

            if parameters:
                # convert v1 to v2
                extract_not_builtin = getattr(param_class, "extract_not_buildin", None)
                if extract_not_builtin is None:
                    raise NotImplementedError(
                        f"param class of `{type(param_class)}` not support v1 style conf"
                    )
                not_builtin_vars = extract_not_builtin()
                role_num = len(role_on_module[local_role])

                # recursive function to convert v1 style to v2 style
                def _convert_v1_to_v2(_conf_v1):
                    _conf_v2 = {}
                    for key, values in _conf_v1.items():
                        # stop here, values support to be a list
                        if key not in not_builtin_vars:
                            if not isinstance(values, list):
                                raise RoleParameterNotListError(
                                    role=local_role, parameter=key
                                )
                            if len(values) != role_num:
                                raise RoleParameterNotConsistencyError(
                                    role=local_role, parameter=key
                                )
                            _conf_v2[key] = values[role_idx]
                        else:
                            _conf_v2[key] = _convert_v1_to_v2(values)
                    return _conf_v2

                parameters = _convert_v1_to_v2(parameters)
                param_class = param_class.update(parameters, not redundant_param_check)

        else:
            raise NotImplementedError(f"conf version = `{conf_version}` is not supported")

        conf["ComponentParam"] = param_class.as_dict()
        param_class.check()

        return conf

    @staticmethod
    def get_job_providers(dsl, provider_detail):
        provider_info = {}
        for component in dsl["components"]:
            module = dsl["components"][component]["module"]
            provider = dsl["components"][component].get("provider")
            if provider:
                provider_msg = provider.split("@", -1)
                if provider[0] == "@":
                    raise ValueError("Provider format should be provider_name@provider_version or provider_name, "
                                     "@provider_version is not supported")
                if len(provider_msg) == 2:
                    name, version = provider.split("@", -1)
                else:
                    name = provider_msg[0]
                    version = RuntimeConfParserUtil.get_component_provider(alias=component,
                                                                           module=module,
                                                                           provider_detail=provider_detail,
                                                                           name=name)


            else:
                name, version = RuntimeConfParserUtil.get_component_provider(alias=component,
                                                                             module=module,
                                                                             provider_detail=provider_detail)

            provider_info.update({component: {
                "module": module,
                "provider": {
                    "name": name,
                    "version": version
                }
            }})

        return provider_info

    @staticmethod
    def get_component_provider(alias, module, provider_detail, detect=True, name=None):
        if module not in provider_detail["components"]:
            if detect:
                raise ValueError(f"component {alias}, module {module}'s provider does not exist")
            else:
                return None

        if name is None:
            name = provider_detail["components"][module]["default_provider"]
            version = provider_detail["provider"][name]["default"]["version"]
            return name, version
        else:
            if name not in provider_detail["components"][module]["support_provider"]:
                raise ValueError(f"Provider {name} does not support, please register in fate-flow")
            version = provider_detail["provider"][name]["default"]["version"]

            return version

    @staticmethod
    def instantiate_component_provider(provider_detail, alias=None, module=None, provider_name=None,
                                       provider_version=None, local_role=None, local_party_id=None,
                                       detect=True, provider_cache=None, job_parameters=None):
        if provider_name and provider_version:
            provider_path = provider_detail["provider"][provider_name][provider_version]["path"]
            provider = provider_utils.get_provider_interface(ComponentProvider(name=provider_name, version=provider_version, path=provider_path))
            if provider_cache is not None:
                if provider_name not in provider_cache:
                    provider_cache[provider_name] = {}

                provider_cache[provider_name][provider_version] = provider

            return provider

        provider_name, provider_version = RuntimeConfParserUtil.get_component_provider(alias=alias,
                                                                                       module=module,
                                                                                       provider_detail=provider_detail,
                                                                                       local_role=local_role,
                                                                                       local_party_id=local_party_id,
                                                                                       job_parameters=job_parameters,
                                                                                       provider_cache=provider_cache,
                                                                                       detect=detect)

        return RuntimeConfParserUtil.instantiate_component_provider(provider_detail,
                                                                    provider_name=provider_name,
                                                                    provider_version=provider_version)


class RuntimeConfParserV1(object):
    @classmethod
    def get_input_parameters(cls, submit_dict):
        if "role_parameters" not in submit_dict:
            return dict()

        roles = submit_dict["role_parameters"].keys()
        if not roles:
            return dict()

        args_input = dict()
        args_data_key = set()
        module = "args"

        for role in roles:
            if not submit_dict["role_parameters"][role].get(module):
                continue
            party_id_list = submit_dict["role"][role]

            args_parameters = submit_dict["role_parameters"][role].get(module)
            args_input[role] = list()

            if "data" in args_parameters:
                dataset = args_parameters.get("data")
                for data_key in dataset:
                    datalist = dataset[data_key]

                    if len(datalist) != len(party_id_list):
                        raise RoleParameterNotConsistencyError(role=role, parameter=data_key)

                    args_data_key.add(data_key)

                    for idx, value in enumerate(datalist):
                        if len(args_input[role]) <= idx:
                            args_input[role].append({module: {"data": dict()}})

                        args_input[role][idx][module]["data"][data_key] = value

        return args_input, args_data_key

    @staticmethod
    def get_job_parameters(submit_dict):
        ret = {}
        job_parameters = submit_dict.get("job_parameters", {})
        for role in submit_dict["role"]:
            party_id_list = submit_dict["role"][role]
            ret[role] = {party_id: copy.deepcopy(job_parameters) for party_id in party_id_list}

        return ret

    @staticmethod
    def generate_predict_conf_template(predict_dsl, train_conf, model_id, model_version):
        if not train_conf.get("role") or not train_conf.get("initiator"):
            raise ValueError("role and initiator should be contain in job's trainconf")

        predict_conf = dict()
        predict_conf["initiator"] = train_conf.get("initiator")
        predict_conf["role"] = train_conf.get("role")

        predict_conf["job_parameters"] = train_conf.get("job_parameters", {})
        predict_conf["job_parameters"]["job_type"] = "predict"
        predict_conf["job_parameters"]["model_id"] = model_id
        predict_conf["job_parameters"]["model_version"] = model_version

        predict_conf["role_parameters"] = {}

        for role in predict_conf["role"]:
            if role not in ["guest", "host"]:
                continue

            args_input = set()
            for _, module_info in predict_dsl.get("components", {}).items():
                data_set = module_info.get("input", {}).get("data", {})
                for data_key in data_set:
                    for data in data_set[data_key]:
                        if data.split(".", -1)[0] == "args":
                            args_input.add(data.split(".", -1)[1])

            predict_conf["role_parameters"][role] = {"args": {"data": {}}}
            fill_template = {}
            for data_key in args_input:
                fill_template[data_key] = [{"name": "name_to_be_filled_" + str(i),
                                            "namespace": "namespace_to_be_filled_" + str(i)}
                                           for i in range(len(predict_conf["role"].get(role)))]

            predict_conf["role_parameters"][role] = {"args": {"data": fill_template}}

        return predict_conf


class RuntimeConfParserV2(object):
    @classmethod
    def get_input_parameters(cls, submit_dict, components=None):
        if submit_dict.get("component_parameters", {}).get("role") is None or components is None:
            return {}

        roles = submit_dict["component_parameters"]["role"].keys()
        if not roles:
            return {}

        input_parameters = {"dsl_version": 2}

        cpn_dict = {}
        for reader_cpn in components:
            cpn_dict[reader_cpn] = {}

        for role in roles:
            role_parameters = submit_dict["component_parameters"]["role"][role]
            input_parameters[role] = [copy.deepcopy(cpn_dict)] * len(submit_dict["role"][role])

            for idx, parameters in role_parameters.items():
                for reader in components:
                    if reader not in parameters:
                        continue

                    if idx == "all":
                        party_id_list = submit_dict["role"][role]
                        for i in range(len(party_id_list)):
                            input_parameters[role][i][reader] = parameters[reader]
                    elif len(idx.split("|")) == 1:
                        input_parameters[role][int(idx)][reader] = parameters[reader]
                    else:
                        id_set = list(map(int, idx.split("|")))
                        for _id in id_set:
                            input_parameters[role][_id][reader] = parameters[reader]

        return input_parameters

    @staticmethod
    def get_job_parameters(submit_dict):
        ret = {}
        job_parameters = submit_dict.get("job_parameters", {})
        common_job_parameters = job_parameters.get("common", {})
        role_job_parameters = job_parameters.get("role", {})
        for role in submit_dict["role"]:
            party_id_list = submit_dict["role"][role]
            if not role_job_parameters:
                ret[role] = {party_id: copy.deepcopy(common_job_parameters) for party_id in party_id_list}
                continue

            ret[role] = {}
            for idx in range(len(party_id_list)):
                role_ids = role_job_parameters.get(role, {}).keys()
                parameters = copy.deepcopy(common_job_parameters)
                for role_id in role_ids:
                    if role_id == "all" or str(idx) in role_id.split("|"):
                        parameters = RuntimeConfParserUtil.merge_dict(parameters,
                                                                      role_job_parameters.get(role, {})[role_id])

                ret[role][party_id_list[idx]] = parameters

        return ret

    @staticmethod
    def generate_predict_conf_template(predict_dsl, train_conf, model_id, model_version):
        if not train_conf.get("role") or not train_conf.get("initiator"):
            raise ValueError("role and initiator should be contain in job's trainconf")

        predict_conf = dict()
        predict_conf["dsl_version"] = 2
        predict_conf["role"] = train_conf.get("role")
        predict_conf["initiator"] = train_conf.get("initiator")

        predict_conf["job_parameters"] = train_conf.get("job_parameters", {})
        predict_conf["job_parameters"]["common"].update({"model_id": model_id,
                                                         "model_version": model_version,
                                                         "job_type": "predict"})

        predict_conf["component_parameters"] = {"role": {}}

        for role in predict_conf["role"]:
            if role not in ["guest", "host"]:
                continue

            reader_components = []
            for module_alias, module_info in predict_dsl.get("components", {}).items():
                if module_info["module"] == "Reader":
                    reader_components.append(module_alias)

            predict_conf["component_parameters"]["role"][role] = dict()
            fill_template = {}
            for idx, reader_alias in enumerate(reader_components):
                fill_template[reader_alias] = {"table": {"name": "name_to_be_filled_" + str(idx),
                                                         "namespace": "namespace_to_be_filled_" + str(idx)}}

            for idx in range(len(predict_conf["role"][role])):
                predict_conf["component_parameters"]["role"][role][str(idx)] = fill_template

        return predict_conf
