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
from fate_flow.utils.dsl_exception import RoleParameterNotConsistencyError, ModuleNotExistError, RoleParameterNotListError


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
    def get_module_name(module, role, component_interface_list):
        for component_interface in component_interface_list:
            if component_interface.has_module(module):
                if component_interface.has_module(module):
                    return component_interface.get_module_name(module, role)

        raise ValueError(f"Can not find module {module}")

    @staticmethod
    def get_component_parameters(component_interface_list,
                                 runtime_conf,
                                 module,
                                 alias,
                                 redundant_param_check,
                                 parse_parameter,
                                 conf_version):
        valid_interface = None
        for component_interface in component_interface_list:
            if component_interface.has_module(module):
                valid_interface = component_interface
                break

        if not valid_interface:
            raise ModuleNotExistError(component=alias, module=module)

        support_roles = valid_interface.get_support_role(module, runtime_conf["role"])
        role_on_module = copy.deepcopy(runtime_conf["role"])
        for role in runtime_conf["role"]:
            if role not in support_roles:
                del role_on_module[role]

        component_conf = {}
        for role in role_on_module:
            party_id_list = role_on_module[role]
            component_conf[role] = []
            for idx, party_id in enumerate(party_id_list):
                conf = dict()
                conf["role"] = role_on_module
                conf["local"] = runtime_conf.get("local", {})
                conf["local"].update({"role": role,
                                      "party_id": party_id})
                conf["module"] = module
                conf["CodePath"] = valid_interface.get_module_name(module, role)
                for key, value in runtime_conf.items():
                    if key not in ["algorithm_parameters", "role_parameters", "component_parameters"]:
                        conf[key] = value

                if not parse_parameter:
                    component_conf[role].append(conf)
                    continue

                common_parameters = runtime_conf.get("component_parameters", {}).get("common", {}) if conf_version == 2 \
                    else runtime_conf.get("algorithm_parameters", {})

                param_class = valid_interface.get_module_param(module, alias)
                if alias in common_parameters:
                    common_parameters = common_parameters[alias]
                    param_class = valid_interface.update_param(param_class,
                                                               common_parameters,
                                                               redundant_param_check,
                                                               module,
                                                               alias)

                if conf_version == 2:
                    role_parameters = runtime_conf.get("component_parameters", {}).get("role", {}).get(role, {})
                    role_ids = role_parameters.keys()
                    for role_id in role_ids:
                        if role_id == "all" or str(idx) in role_id.split("|"):
                            parameters = role_parameters[role_id].get(alias, {})
                            if not parameters:
                                continue
                            param_class = valid_interface.update_param(param_class,
                                                                       parameters,
                                                                       redundant_param_check,
                                                                       module,
                                                                       alias
                                                                       )
                else:
                    # query if backend interface support dsl v1
                    if hasattr(valid_interface, "get_not_builtin_types_for_dsl_v1"):
                        v1_parameters = runtime_conf.get("role_parameters", {}).get(role, {}).get(alias, {})
                        not_builtin_vars = valid_interface.get_not_builtin_types_for_dsl_v1(param_class)
                        if v1_parameters:
                            v2_parameters = RuntimeConfParserUtil.change_conf_v1_to_v2(v1_parameters, not_builtin_vars, idx, role, len(role_on_module[role]))
                            param_class = valid_interface.update_param(param_class,
                                                                       v2_parameters,
                                                                       redundant_param_check,
                                                                       module,
                                                                       alias
                                                                       )
                valid_interface.check_param(param_class)
                conf["ComponentParam"] = valid_interface.change_param_to_dict(param_class)
                component_conf[role].append(conf)

        return component_conf

    @staticmethod
    def change_conf_v1_to_v2(v1_conf, not_builtin_vars, idx, role, role_num):
        v2_conf = {}
        for key, val_list in v1_conf.items():
            if key not in not_builtin_vars:
                if not isinstance(val_list, list):
                    raise RoleParameterNotListError(role=role, parameter=key)

                if len(val_list) != role_num:
                    raise RoleParameterNotConsistencyError(role=role, parameter=key)

                v2_conf[key] = val_list[idx]

            else:
                v2_conf[key] = RuntimeConfParserUtil.change_conf_v1_to_v2(val_list, not_builtin_vars, idx, role, role_num)

        return v2_conf


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

