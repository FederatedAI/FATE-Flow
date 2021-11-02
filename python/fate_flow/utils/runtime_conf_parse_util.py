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
from fate_arch.abc import Components
from fate_flow.component_env_utils import provider_utils
from fate_flow.entity import ComponentProvider
from fate_flow.db.component_registry import ComponentRegistry


class RuntimeConfParserUtil(object):
    @classmethod
    def get_input_parameters(cls, submit_dict, components=None):
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
    def generate_predict_conf_template(predict_dsl, train_conf, model_id, model_version):
        return RuntimeConfParserV2.generate_predict_conf_template(predict_dsl, train_conf, model_id, model_version)

    @staticmethod
    def get_module_name(module, role, provider: Components):
        return provider.get(module, ComponentRegistry.get_provider_components(provider.provider_name, provider.provider_version)).get_run_obj_name(role)

    @staticmethod
    def get_component_parameters(
        provider,
        runtime_conf,
        module,
        alias,
        redundant_param_check,
        local_role,
        local_party_id,
        parse_user_specified_only,
        pre_parameters=None
    ):
        provider_components = ComponentRegistry.get_provider_components(
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

        user_specified_parameters = dict()

        if pre_parameters:
            if parse_user_specified_only:
                user_specified_parameters.update(
                    pre_parameters.get("ComponentParam", {})
                )
            else:
                param_class = param_class.update(
                    pre_parameters.get("ComponentParam", {})
                )

        common_parameters = (
            runtime_conf.get("component_parameters", {}).get("common", {}).get(alias, {})
        )

        if parse_user_specified_only:
            user_specified_parameters.update(common_parameters)
        else:
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
                parameters = role_id_parameters.get(alias, {})
                if parse_user_specified_only:
                    user_specified_parameters.update(parameters)
                else:
                    param_class.update(parameters, not redundant_param_check)

        if not parse_user_specified_only:
            conf["ComponentParam"] = param_class.as_dict()
            param_class.check()
        else:
            conf["ComponentParam"] = user_specified_parameters

        return conf

    @staticmethod
    def convert_parameters_v1_to_v2(party_idx, parameter_v1, not_builtin_vars):
        parameter_v2 = {}
        for key, values in parameter_v1.items():
            # stop here, values support to be a list
            if key not in not_builtin_vars:
                parameter_v2[key] = values[party_idx]
            else:
                parameter_v2[key] = RuntimeConfParserUtil.convert_parameters_v1_to_v2(party_idx, values, not_builtin_vars)

        return parameter_v2

    @staticmethod
    def get_v1_role_parameters(provider, component, runtime_conf, dsl):
        component_role_parameters = dict()
        if "role_parameters" not in runtime_conf:
            return component_role_parameters

        role_parameters = runtime_conf["role_parameters"]
        module = dsl["components"][component]["module"]
        if module == "Reader":
            data_key = dsl["components"][component]["output"]["data"][0]

            for role, role_params in role_parameters.items():
                if not role_params.get("args", {}).get("data", {}).get(data_key):
                    continue

                component_role_parameters[role] = dict()
                dataset = role_params["args"]["data"][data_key]
                for idx, table in enumerate(dataset):
                    component_role_parameters[role][str(idx)] = {component: {"table": table}}
        else:
            provider_components = ComponentRegistry.get_provider_components(
                provider.provider_name, provider.provider_version
            )
            param_class = provider.get(module, provider_components).get_param_obj(component)
            extract_not_builtin = getattr(param_class, "extract_not_builtin", None)
            not_builtin_vars = extract_not_builtin() if extract_not_builtin is not None else {}

            for role, role_params in role_parameters.items():
                params = role_params.get(component, {})
                if not params:
                    continue

                component_role_parameters[role] = dict()
                party_num = len(runtime_conf["role"][role])

                for party_idx in range(party_num):
                    party_param = RuntimeConfParserUtil.convert_parameters_v1_to_v2(party_idx, params, not_builtin_vars)
                    component_role_parameters[role][str(party_idx)] = {component: party_param}

        return component_role_parameters

    @staticmethod
    def get_job_providers(dsl, provider_detail):
        provider_info = {}
        global_provider_name = None
        global_provider_version = None
        if "provider" in dsl:
            global_provider_msg = dsl["provider"].split("@", -1)
            if global_provider_msg[0] == "@" or len(global_provider_msg) > 2:
                raise ValueError("Provider format should be provider_name@provider_version or provider_name, "
                                 "@provider_version is not supported")
            if len(global_provider_msg) == 1:
                global_provider_name = global_provider_msg[0]
            else:
                global_provider_name, global_provider_version = global_provider_msg

        for component in dsl["components"]:
            module = dsl["components"][component]["module"]
            provider = dsl["components"][component].get("provider")
            name, version = None, None
            if provider:
                provider_msg = provider.split("@", -1)
                if provider[0] == "@" or len(provider_msg) > 2:
                    raise ValueError("Provider format should be provider_name@provider_version or provider_name, "
                                     "@provider_version is not supported")
                if len(provider_msg) == 2:
                    name, version = provider.split("@", -1)
                else:
                    name = provider_msg[0]

            if not name:
                if global_provider_name:
                    name = global_provider_name
                    version = global_provider_version

            if name and name not in provider_detail["components"][module]["support_provider"]:
                raise ValueError(f"Provider: {name} does not support in {module}, please register")
            if version and version not in provider_detail["providers"][name]:
                raise ValueError(f"Provider: {name} version: {version} does not support in {module}, please register")

            if name and not version:
                version = RuntimeConfParserUtil.get_component_provider(alias=component,
                                                                       module=module,
                                                                       provider_detail=provider_detail,
                                                                       name=name)
            elif not name and not version:
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
            version = provider_detail["providers"][name]["default"]["version"]
            return name, version
        else:
            if name not in provider_detail["components"][module]["support_provider"]:
                raise ValueError(f"Provider {name} does not support, please register in fate-flow")
            version = provider_detail["providers"][name]["default"]["version"]

            return version

    @staticmethod
    def instantiate_component_provider(provider_detail, alias=None, module=None, provider_name=None,
                                       provider_version=None, local_role=None, local_party_id=None,
                                       detect=True, provider_cache=None, job_parameters=None):
        if provider_name and provider_version:
            provider_path = provider_detail["providers"][provider_name][provider_version]["path"]
            provider = provider_utils.get_provider_interface(ComponentProvider(name=provider_name,
                                                                               version=provider_version,
                                                                               path=provider_path,
                                                                               class_path=ComponentRegistry.get_default_class_path()))
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

    @classmethod
    def merge_predict_runtime_conf(cls, train_conf, predict_conf):
        runtime_conf = copy.deepcopy(train_conf)
        train_role = train_conf.get("role")
        predict_role = predict_conf.get("role")
        if len(train_conf) < len(predict_role):
            raise ValueError(f"Predict roles is {predict_role}, train roles is {train_conf}, "
                             "predict roles should be subset of train role")

        for role in train_role:
            if role not in predict_role:
                del runtime_conf["role"][role]

                if runtime_conf.get("job_parameters", {}).get("role", {}).get(role):
                    del runtime_conf["job_parameters"]["role"][role]

                if runtime_conf.get("component_parameters", {}).get("role", {}).get(role):
                    del runtime_conf["component_parameters"]["role"][role]

                continue

            train_party_ids = train_role[role]
            predict_party_ids = predict_role[role]

            diff = False
            for idx, party_id in enumerate(predict_party_ids):
                if party_id not in train_party_ids:
                    raise ValueError(f"Predict role: {role} party_id: {party_id} not occurs in training")
                if train_party_ids[idx] != party_id:
                    diff = True

            if not diff and len(train_party_ids) == len(predict_party_ids):
                continue

            for p_type in ["job_parameters", "component_parameters"]:
                if not runtime_conf.get(p_type, {}).get("role", {}).get(role):
                    continue

                conf = runtime_conf[p_type]["role"][role]
                party_keys = conf.keys()
                new_conf = {}
                for party_key in party_keys:
                    party_list = party_key.split("|", -1)
                    new_party_list = []
                    for party in party_list:
                        party_id = train_party_ids[int(party)]
                        if party_id in predict_party_ids:
                            new_idx = predict_party_ids.index(party_id)
                            new_party_list.append(str(new_idx))

                    if not new_party_list:
                        continue

                    new_party_key = new_party_list[0] if len(new_party_list) == 1 else "|".join(new_party_list)

                    if new_party_key not in new_conf:
                        new_conf[new_party_key] = {}
                    new_conf[new_party_key].update(conf[party_key])

                runtime_conf[p_type]["role"][role] = new_conf

        runtime_conf = cls.merge_dict(runtime_conf, predict_conf)

        return runtime_conf


class RuntimeConfParserV1(object):
    @staticmethod
    def get_job_parameters(submit_dict):
        ret = {}
        job_parameters = submit_dict.get("job_parameters", {})
        for role in submit_dict["role"]:
            party_id_list = submit_dict["role"][role]
            ret[role] = {party_id: copy.deepcopy(job_parameters) for party_id in party_id_list}

        return ret


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
