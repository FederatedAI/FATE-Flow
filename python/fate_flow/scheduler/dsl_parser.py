#!/usr/bin/env python
# -*- coding: utf-8 -*-

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
################################################################################
#
#
################################################################################

# =============================================================================
# DSL PARSER
# =============================================================================

import copy
import json

from fate_flow.settings import stat_logger
from fate_flow.utils.dsl_exception import DSLNotExistError, ComponentFieldNotExistError, \
    ModuleFieldNotExistError, ComponentInputTypeError, \
    InputComponentNotExistError, InputNameNotExistError, ComponentInputDataTypeError, \
    ComponentInputValueTypeError, \
    ComponentNotExistError, ModeError, DataNotExistInSubmitConfError, ComponentOutputTypeError, \
    ComponentOutputKeyTypeError, LoopError, ComponentMultiMappingError, NamingIndexError, \
    NamingError, NamingFormatError, DeployComponentNotExistError, ModuleNotExistError
from fate_flow.utils.runtime_conf_parse_util import RuntimeConfParserUtil


class Component(object):
    def __init__(self):
        self.module = None
        self.name = None
        self.upstream = []
        self.downstream = []
        self.role_parameters = {}
        self.input = {}
        self.output = {}
        self.component_provider = None

    def copy(self):
        copy_obj = Component()
        copy_obj.set_module(self.module)
        copy_obj.set_name(self.name)
        copy_obj.set_input(self.input)
        copy_obj.set_downstream(self.downstream)
        copy_obj.set_upstream(self.upstream)
        copy_obj.set_role_parameters(self.role_parameters)
        copy_obj.set_output(self.output)

        return copy_obj

    def set_input(self, inp):
        self.input = inp

    def get_input(self):
        return self.input

    def set_output(self, output):
        self.output = output

    def get_output(self):
        return self.output

    def get_module(self):
        return self.module

    def set_component_provider(self, interface):
        self.component_provider = interface

    def get_component_provider(self):
        return self.component_provider

    def get_name(self):
        return self.name

    def get_upstream(self):
        return self.upstream

    def get_downstream(self):
        return self.downstream

    def set_name(self, name):
        self.name = name

    def set_module(self, module):
        self.module = module

    def set_upstream(self, upstream):
        self.upstream = upstream

    def set_downstream(self, downstream):
        self.downstream = downstream

    def set_role_parameters(self, role_parameters):
        self.role_parameters = role_parameters

    def get_role_parameters(self):
        return self.role_parameters


class BaseDSLParser(object):
    def __init__(self):
        self.dsl = None
        self.mode = "train"
        self.components = []
        self.component_name_index = {}
        self.component_upstream = []
        self.component_downstream = []
        self.train_input_model = {}
        self.in_degree = []
        self.topo_rank = []
        self.predict_dsl = {}
        self.runtime_conf = {}
        self.pipeline_runtime_conf = {}
        self.graph_dependency = None
        self.args_input = None
        self.args_data_key = None
        self.next_component_to_topo = set()
        self.job_parameters = {}
        self.provider_cache = {}
        self.job_providers = {}
        self.version = 2
        self.local_role = None
        self.local_party_id = None
        self.predict_runtime_conf = {}

    def _init_components(self, mode="train", version=1, **kwargs):
        if not self.dsl:
            raise DSLNotExistError("")

        components = self.dsl.get("components")

        if components is None:
            raise ComponentFieldNotExistError()

        for name in components:
            if "module" not in components[name]:
                raise ModuleFieldNotExistError(component=name)

            module = components[name]["module"]

            new_component = Component()
            new_component.set_name(name)
            new_component.set_module(module)
            self.component_name_index[name] = len(self.component_name_index)
            self.components.append(new_component)

        if version == 2 or mode == "train":
            self._check_component_valid_names()

    def _check_component_valid_names(self):
        for component in self.components:
            name = component.get_name()
            for chk in name:
                if chk.isalpha() or chk in ["_", "-"] or chk.isdigit():
                    continue
                else:
                    raise NamingFormatError(component=name)

    def _find_dependencies(self, mode="train", version=1):
        self.component_downstream = [[] for i in range(len(self.components))]
        self.component_upstream = [[] for i in range(len(self.components))]

        components_details = self.dsl.get("components")
        components_output = self._find_outputs(self.dsl)

        for name in self.component_name_index.keys():
            idx = self.component_name_index.get(name)
            upstream_input = components_details.get(name).get("input")
            downstream_output = components_details.get(name).get("output", {})

            self.components[idx].set_output(downstream_output)
            if upstream_input is None:
                continue
            elif not isinstance(upstream_input, dict):
                raise ComponentInputTypeError(component=name)
            else:
                self.components[idx].set_input(upstream_input)

            if mode == "train":
                input_keywords = {"model": "model", "isometric_model": "model", "cache": "cache"}
            else:
                input_keywords = {"cache": "cache"}

            for keyword, out_type in input_keywords.items():
                if keyword in upstream_input:
                    input_list = upstream_input.get(keyword)

                    if not isinstance(input_list, list):
                        raise ComponentInputValueTypeError(component=name, value_type="model",
                                                           other_info=input_list)

                    for _input in input_list:
                        input_component = _input.split(".", -1)[0]
                        input_model_name = _input.split(".")[-1]
                        if input_component not in self.component_name_index:
                            raise InputComponentNotExistError(component=name, value_type=keyword, input=input_component)
                        else:
                            if input_component not in components_output or out_type not in components_output[input_component]:
                                raise InputNameNotExistError(component=name, input=input_component,
                                                             value_type=keyword, other_info=input_model_name)

                            idx_dependency = self.component_name_index.get(input_component)
                            self.component_downstream[idx_dependency].append(name)
                            self.component_upstream[idx].append(input_component)

                            if keyword == "model" or keyword == "cache":
                                self.train_input_model[name] = input_component

            if "data" in upstream_input:
                data_dict = upstream_input.get("data")
                if not isinstance(data_dict, dict):
                    raise ComponentInputDataTypeError(component=name)

                for data_set in data_dict:
                    if not isinstance(data_dict.get(data_set), list):
                        raise ComponentInputValueTypeError(component=name, value_type="data",
                                                           other_info=data_dict.get(data_set))

                    if version == 2 and data_set not in ["data", "train_data", "validate_data", "test_data",
                                                         "eval_data"]:
                        stat_logger.warning(
                            "DSLParser Warning: make sure that input data's data key should be in {}, but {} found".format(
                                ["data", "train_data", "validate_data", "test_data", "eval_data"], data_set))
                    for data_key in data_dict.get(data_set):
                        input_component = data_key.split(".", -1)[0]
                        input_data_name = data_key.split(".", -1)[-1]

                        if input_component not in self.component_name_index:
                            raise InputComponentNotExistError(component=name, value_type="data",
                                                              input=input_component)
                        else:
                            if input_component not in components_output \
                                    or "data" not in components_output[input_component] \
                                    or input_data_name not in components_output[input_component]["data"]:
                                raise InputNameNotExistError(component=name, input=input_component,
                                                             value_type="data", other_info=input_data_name)

                            idx_dependency = self.component_name_index.get(input_component)
                            self.component_downstream[idx_dependency].append(name)
                            self.component_upstream[idx].append(input_component)

        self.in_degree = [0 for i in range(len(self.components))]
        for i in range(len(self.components)):
            if self.component_downstream[i]:
                self.component_downstream[i] = list(set(self.component_downstream[i]))

            if self.component_upstream[i]:
                self.component_upstream[i] = list(set(self.component_upstream[i]))
                self.in_degree[self.component_name_index.get(self.components[i].get_name())] = len(
                    self.component_upstream[i])

        self._check_dag_dependencies()

        for i in range(len(self.components)):
            self.components[i].set_upstream(self.component_upstream[i])
            self.components[i].set_downstream(self.component_downstream[i])

    def _init_component_setting(self,
                                component,
                                provider_detail,
                                provider_name,
                                provider_version,
                                local_role,
                                local_party_id,
                                runtime_conf,
                                redundant_param_check=True,
                                parse_user_specified_only=False,
                                previous_parameters=None
                                ):
        """
        init top input
        """
        provider = RuntimeConfParserUtil.instantiate_component_provider(provider_detail,
                                                                        provider_name=provider_name,
                                                                        provider_version=provider_version)

        pos = self.component_name_index[component]
        module = self.components[pos].get_module()

        parent_path = [component]
        cur_component = component
        isometric_component = None

        while True:
            if self.train_input_model.get(cur_component, None) is None:
                break
            else:
                is_warm_start = self._is_warm_start(cur_component)
                is_same_module = True
                input_component = self.train_input_model.get(cur_component)
                input_pos = self.component_name_index[input_component]
                if self.components[input_pos].get_module() != module:
                    is_same_module = False

                if not is_warm_start and is_same_module:
                    cur_component = self.train_input_model.get(cur_component)
                    parent_path.append(cur_component)
                else:
                    isometric_component = input_component
                    break

        pre_parameters = {}
        if previous_parameters is not None:
            if not isometric_component:
                pre_parameters = previous_parameters.get(cur_component, {})
            else:
                pre_parameters = previous_parameters.get(isometric_component, {})

        role_parameters = RuntimeConfParserUtil.get_component_parameters(provider,
                                                                         runtime_conf,
                                                                         module,
                                                                         cur_component,
                                                                         redundant_param_check=redundant_param_check,
                                                                         local_role=local_role,
                                                                         local_party_id=local_party_id,
                                                                         parse_user_specified_only=parse_user_specified_only,
                                                                         pre_parameters=pre_parameters)

        """
        if previous_parameters is not None:
            if not isometric_component:
                pre_parameters = previous_parameters.get(cur_component, {})
            else:
                pre_parameters = previous_parameters.get(isometric_component, {})

            if pre_parameters:
                role_parameters = RuntimeConfParserUtil.merge_dict(pre_parameters, role_parameters)
        """

        for component in parent_path:
            idx = self.component_name_index.get(component)
            self.components[idx].set_component_provider(provider)
            self.components[idx].set_role_parameters(role_parameters)

        return role_parameters

    def _is_warm_start(self, component_name):
        component_idx = self.component_name_index.get(component_name)
        upstream_inputs = self.components[component_idx].get_input()
        if not upstream_inputs:
            return False

        return "train_data" in upstream_inputs.get("data", {}) and "model" in upstream_inputs

    def parse_component_parameters(self, component_name, provider_detail, provider_name, provider_version, local_role,
                                   local_party_id, previous_parameters=None):
        if self.mode == "predict":
            runtime_conf = self.predict_runtime_conf
        else:
            runtime_conf = self.runtime_conf

        redundant_param_check = True
        parameters = self._init_component_setting(component_name,
                                                  provider_detail,
                                                  provider_name,
                                                  provider_version,
                                                  local_role,
                                                  local_party_id,
                                                  runtime_conf,
                                                  redundant_param_check,
                                                  parse_user_specified_only=False,
                                                  previous_parameters=previous_parameters)

        return parameters

    def get_component_info(self, component_name):
        if component_name not in self.component_name_index:
            raise ComponentNotExistError(component=component_name)

        idx = self.component_name_index.get(component_name)
        return self.components[idx]

    def get_upstream_dependent_components(self, component_name):
        dependent_component_names = self.get_component_info(component_name).get_upstream()
        dependent_components = []
        for up_cpn in dependent_component_names:
            up_cpn_idx = self.component_name_index.get(up_cpn)
            dependent_components.append(self.components[up_cpn_idx])

        return dependent_components

    def get_downstream_dependent_components(self, component_name):
        component_idx = self.component_name_index.get(component_name)
        downstream_components = []
        for cpn in self.component_downstream[component_idx]:
            down_cpn_idx = self.component_name_index.get(cpn)
            downstream_components.append(self.components[down_cpn_idx])

        return downstream_components

    def get_topology_components(self):
        topo_components = []
        for i in range(len(self.topo_rank)):
            topo_components.append(self.components[self.topo_rank[i]])

        return topo_components

    @staticmethod
    def _find_outputs(dsl):
        outputs = {}

        components_details = dsl.get("components")

        for name in components_details.keys():
            if "output" not in components_details.get(name):
                continue

            component_output = components_details.get(name).get("output")
            output_keys = ["data", "model", "cache"]

            if not isinstance(component_output, dict):
                raise ComponentOutputTypeError(component=name, other_info=component_output)

            for key in output_keys:
                if key not in component_output:
                    continue

                out_v = component_output.get(key)
                if not isinstance(out_v, list):
                    raise ComponentOutputKeyTypeError(component=name, other_info=key)

                if name not in outputs:
                    outputs[name] = {}

                outputs[name][key] = out_v

        return outputs

    def _check_dag_dependencies(self):
        in_degree = copy.deepcopy(self.in_degree)
        stack = []

        for i in range(len(self.components)):
            if in_degree[i] == 0:
                stack.append(i)

        tot_nodes = 0

        while len(stack) > 0:
            idx = stack.pop()
            tot_nodes += 1
            self.topo_rank.append(idx)

            for down_name in self.component_downstream[idx]:
                down_idx = self.component_name_index.get(down_name)
                in_degree[down_idx] -= 1

                if in_degree[down_idx] == 0:
                    stack.append(down_idx)

        if tot_nodes != len(self.components):
            stack = []
            vis = [False for i in range(len(self.components))]
            for i in range(len(self.components)):
                if vis[i]:
                    continue
                loops = []
                self._find_loop(i, vis, stack, loops)
                raise LoopError(loops)

    def _find_loop(self, u, vis, stack, loops):
        vis[u] = True
        stack.append(u)
        for down_name in self.component_downstream[u]:
            if loops:
                return

            v = self.component_name_index.get(down_name)

            if v not in stack:
                if not vis[v]:
                    self._find_loop(v, vis, stack, loops)
            else:
                index = stack.index(v)
                for node in stack[index:]:
                    loops.append(self.components[node].get_name())

                return

        stack.pop(-1)

    def prepare_graph_dependency_info(self):
        dependence_dict = {}
        component_module = {}
        for component in self.components:
            name = component.get_name()
            module = component.get_module()
            component_module[name] = module
            if not component.get_input():
                continue
            dependence_dict[name] = []
            inputs = component.get_input()
            if "data" in inputs:
                data_input = inputs["data"]
                for data_key, data_list in data_input.items():
                    for dataset in data_list:
                        up_component_name = dataset.split(".", -1)[0]
                        up_pos = self.component_name_index.get(up_component_name)
                        up_component = self.components[up_pos]
                        data_name = dataset.split(".", -1)[1]
                        if up_component.get_output().get("data"):
                            data_pos = up_component.get_output().get("data").index(data_name)
                        else:
                            data_pos = 0

                        if data_key == "data" or data_key == "train_data":
                            data_type = data_key
                        else:
                            data_type = "validate_data"

                        dependence_dict[name].append({"component_name": up_component_name,
                                                      "type": data_type,
                                                      "up_output_info": ["data", data_pos]})

            input_keyword_type_mapping = {"model": "model",
                                          "isometric_model": "model",
                                          "cache": "cache"}
            for keyword, v_type in input_keyword_type_mapping.items():
                if keyword in inputs:
                    input_list = inputs[keyword]
                    for _input in input_list:
                        up_component_name = _input.split(".", -1)[0]
                        if up_component_name == "pipeline":
                            continue

                        link_alias = _input.split(".", -1)[1]
                        up_pos = self.component_name_index.get(up_component_name)
                        up_component = self.components[up_pos]
                        if up_component.get_output().get(v_type):
                            dep_pos = up_component.get_output().get(v_type).index(link_alias)
                        else:
                            dep_pos = 0
                        dependence_dict[name].append({"component_name": up_component_name,
                                                      "type": v_type,
                                                      "up_output_info": [v_type, dep_pos]})

            if not dependence_dict[name]:
                del dependence_dict[name]

        component_list = [None for i in range(len(self.components))]
        topo_rank_reverse_mapping = {}
        for i in range(len(self.topo_rank)):
            topo_rank_reverse_mapping[self.topo_rank[i]] = i

        for key, value in self.component_name_index.items():
            topo_rank_idx = topo_rank_reverse_mapping[value]
            component_list[topo_rank_idx] = key

        base_dependency = {"component_list": component_list,
                           "dependencies": dependence_dict,
                           "component_module": component_module,
                           "component_need_run": {}}

        self.graph_dependency = base_dependency

    def get_dsl_hierarchical_structure(self):
        max_depth = [0] * len(self.components)
        for idx in range(len(self.topo_rank)):
            vertex = self.topo_rank[idx]
            for down_name in self.component_downstream[vertex]:
                down_vertex = self.component_name_index.get(down_name)
                max_depth[down_vertex] = max(max_depth[down_vertex], max_depth[vertex] + 1)

        max_dep = max(max_depth)
        hierarchical_structure = [[] for i in range(max_dep + 1)]
        name_component_maps = {}

        for component in self.components:
            name = component.get_name()
            vertex = self.component_name_index.get(name)
            hierarchical_structure[max_depth[vertex]].append(name)

            name_component_maps[name] = component

        return name_component_maps, hierarchical_structure

    def get_dependency(self):
        return self.graph_dependency

    def get_dependency_with_parameters(self, component_parameters):
        return self.extract_need_run_status(self.graph_dependency, component_parameters)

    def extract_need_run_status(self, graph_dependency, component_parameters):
        for rank in range(len(self.topo_rank)):
            idx = self.topo_rank[rank]
            name = self.components[idx].get_name()
            parameters = component_parameters.get(name)

            if not parameters:
                graph_dependency["component_need_run"][name] = False
            else:
                if self.train_input_model.get(name, None) is None:
                    param_name = "ComponentParam"
                    if parameters.get(param_name) is None \
                        or parameters[param_name].get("need_run") is False:
                        graph_dependency["component_need_run"][name] = False
                    else:
                        graph_dependency["component_need_run"][name] = True
                else:
                    input_model_name = self.train_input_model.get(name)
                    graph_dependency["component_need_run"][name] = graph_dependency["component_need_run"][
                            input_model_name]

        return graph_dependency

    @staticmethod
    def verify_dsl(dsl, mode="train"):
        dsl_parser = DSLParserV2()
        dsl_parser.dsl = dsl
        dsl_parser._init_components(mode=mode, version=2)
        dsl_parser._find_dependencies(mode=mode, version=2)

    @staticmethod
    def verify_dsl_reusability(reused_dsl, new_dsl, reused_components):
        # step 1, verify new dsl
        dsl_parser = DSLParserV2()
        dsl_parser.dsl = new_dsl
        dsl_parser._init_components(mode="train", version=2)
        dsl_parser._find_dependencies(mode="train", version=2)

        # step 2, verify reused components is a sub-graph
        reused_components = set(reused_components)
        # reused_components = set(reused_dsl["components"]) & set(new_dsl["components"])
        for cpn in reused_components:
            validate_key = ["input", "output", "provider"]
            for vk in validate_key:
                config_old = reused_dsl["components"][cpn].get(vk, None)
                config_new = new_dsl["components"][cpn].get(vk, None)
                if config_old != config_new:
                    raise ValueError(f"Component {cpn}'s {vk} should be same, but old is {config_old}, new is {config_new}")

            inputs = reused_dsl["components"][cpn].get("input", {})
            list_dep_key = ["cache", "model", "isometric_model"]
            for dep_key in list_dep_key:
                dep_list = inputs.get(dep_key, [])
                for dep in dep_list:
                    input_dep = dep.split(".", -1)[0]
                    if input_dep not in reused_components:
                        raise ValueError(f"Component {cpn}'s {dep_key} input {input_dep} should be reused")

            data_dep = inputs.get("data", {})
            for data_key, data_list in data_dep.items():
                for dep in data_list:
                    input_dep = dep.split(".", -1)[0]
                    if input_dep not in reused_components:
                        raise ValueError(f"Component {cpn}'s {data_key} input {input_dep} should be reused")

    @staticmethod
    def deploy_component(components, train_dsl, provider_update_dsl=None):
        training_cpns = set(train_dsl.get("components").keys())
        deploy_cpns = set(components)
        if len(deploy_cpns & training_cpns) != len(deploy_cpns):
            raise DeployComponentNotExistError(msg=deploy_cpns - training_cpns)

        dsl_parser = DSLParserV2()
        dsl_parser.dsl = train_dsl
        dsl_parser._init_components()
        dsl_parser._find_dependencies(version=2)
        dsl_parser._auto_deduction(deploy_cpns=deploy_cpns, version=2, erase_top_data_input=True)

        dsl_parser.update_predict_dsl_provider(train_dsl)
        if provider_update_dsl:
            dsl_parser.update_predict_dsl_provider(provider_update_dsl)
        return dsl_parser.predict_dsl

    def update_predict_dsl_provider(self, dsl):
        for component in dsl["components"]:
            provider = dsl["components"][component].get("provider")
            if provider and component in self.predict_dsl["components"]:
                self.predict_dsl["components"][component]["provider"] = provider

        if "provider" in dsl:
            self.predict_dsl["provider"] = dsl["provider"]

    def _auto_deduction(self, deploy_cpns=None, version=1, erase_top_data_input=False):
        self.predict_dsl = {"components": {}}
        self.predict_components = []
        mapping_list = {}
        for i in range(len(self.topo_rank)):
            self.predict_components.append(self.components[self.topo_rank[i]].copy())
            mapping_list[self.predict_components[-1].get_name()] = i

        output_data_maps = {}
        for i in range(len(self.predict_components)):
            name = self.predict_components[i].get_name()
            module = self.predict_components[i].get_module()

            if module == "Reader":
                if version != 2:
                    raise ValueError("Reader component can only be set in dsl_version 2")

            if self.get_need_deploy_parameter(name=name, deploy_cpns=deploy_cpns):
                self.predict_dsl["components"][name] = {"module": self.predict_components[i].get_module()}
                """replace output model to pipeline"""
                if "output" in self.dsl["components"][name]:
                    model_list = self.dsl["components"][name]["output"].get("model", None)
                    if model_list is not None:
                        if "input" not in self.predict_dsl["components"][name]:
                            self.predict_dsl["components"][name]["input"] = {}

                        replace_model = [".".join(["pipeline", name, model]) for model in model_list]
                        self.predict_dsl["components"][name]["input"]["model"] = replace_model

                    for out_key, out_val in self.dsl["components"][name]["output"].items():
                        if out_val is not None and out_key != "model":
                            if "output" not in self.predict_dsl["components"][name]:
                                self.predict_dsl["components"][name]["output"] = {}

                            self.predict_dsl["components"][name]["output"][out_key] = out_val

                if "input" in self.dsl["components"][name]:
                    if "input" not in self.predict_dsl["components"][name]:
                        self.predict_dsl["components"][name]["input"] = {}

                    if "data" in self.dsl["components"][name]["input"]:
                        self.predict_dsl["components"][name]["input"]["data"] = {}
                        for data_key, data_value in self._gen_predict_data_mapping():
                            if data_key not in self.dsl["components"][name]["input"]["data"]:
                                continue

                            data_set = self.dsl["components"][name]["input"]["data"].get(data_key)
                            self.predict_dsl["components"][name]["input"]["data"][data_value] = []
                            for input_data in data_set:
                                if version == 1 and input_data.split(".")[0] == "args":
                                    new_input_data = "args.eval_data"
                                    self.predict_dsl["components"][name]["input"]["data"][data_value].append(new_input_data)
                                elif version == 2 and input_data.split(".")[0] == "args":
                                    self.predict_dsl["components"][name]["input"]["data"][data_value].append(input_data)
                                elif version == 2 and self.dsl["components"][input_data.split(".")[0]].get("module") == "Reader":
                                    self.predict_dsl["components"][name]["input"]["data"][data_value].append(input_data)
                                else:
                                    pre_name = input_data.split(".")[0]
                                    data_suffix = input_data.split(".")[1]
                                    if self.get_need_deploy_parameter(name=pre_name, deploy_cpns=deploy_cpns):
                                        self.predict_dsl["components"][name]["input"]["data"][data_value].append(input_data)
                                    else:
                                        self.predict_dsl["components"][name]["input"]["data"][data_value].extend(
                                            output_data_maps[pre_name][data_suffix])

                            break

                        if "cache" in self.dsl["components"][name]["input"]:
                            cache_set = self.dsl["components"][name]["input"]["cache"]
                            self.predict_dsl["components"][name]["input"]["cache"] = []
                            for input_cache in cache_set:
                                pre_name, cache_suffix = input_cache.split(".")[:2]
                                input_deploy = self.get_need_deploy_parameter(name=pre_name, deploy_cpns=deploy_cpns)
                                if version == 1 and not input_deploy:
                                    raise ValueError("In dsl v1, if cache is enabled, input component should be deploy")
                                self.predict_dsl["components"][name]["input"]["cache"].append(input_cache)

                        if version == 2 and erase_top_data_input:
                            input_dep = {}
                            for data_key, data_set in self.predict_dsl["components"][name]["input"]["data"].items():
                                final_data_set = []
                                for input_data in data_set:
                                    cpn_alias = input_data.split(".")[0]
                                    if cpn_alias in self.predict_dsl["components"]:
                                        final_data_set.append(input_data)

                                if final_data_set:
                                    input_dep[data_key] = final_data_set

                            if not input_dep:
                                del self.predict_dsl["components"][name]["input"]["data"]
                            else:
                                self.predict_dsl["components"][name]["input"]["data"] = input_dep

            else:
                name = self.predict_components[i].get_name()
                input_data, output_data = None, None

                if "input" in self.dsl["components"][name] and "data" in self.dsl["components"][name]["input"]:
                    input_data = self.dsl["components"][name]["input"].get("data")

                if "output" in self.dsl["components"][name] and "data" in self.dsl["components"][name]["output"]:
                    output_data = self.dsl["components"][name]["output"].get("data")

                if output_data is None or input_data is None:
                    continue

                output_data_maps[name] = {}
                for output_data_str in output_data:
                    if "train_data" in input_data or "eval_data" in input_data or "test_data" in input_data:
                        if "train_data" in input_data:
                            up_input_data = input_data.get("train_data")[0]
                        elif "eval_data" in input_data:
                            up_input_data = input_data.get("eval_data")[0]
                        else:
                            up_input_data = input_data.get("test_data")[0]
                    elif "data" in input_data:
                        up_input_data = input_data.get("data")[0]
                    else:
                        raise ValueError("train data or eval data or validate data or data should be set")

                    up_input_data_component_name = up_input_data.split(".", -1)[0]
                    if up_input_data_component_name == "args" \
                            or self.get_need_deploy_parameter(name=up_input_data_component_name, deploy_cpns=deploy_cpns):
                        output_data_maps[name][output_data_str] = [up_input_data]
                    elif self.components[self.component_name_index.get(up_input_data_component_name)].get_module() == "Reader":
                        output_data_maps[name][output_data_str] = [up_input_data]
                    else:
                        up_input_data_suf = up_input_data.split(".", -1)[-1]
                        output_data_maps[name][output_data_str] = output_data_maps[up_input_data_component_name][up_input_data_suf]

    def run(self, *args, **kwargs):
        pass

    def get_runtime_conf(self):
        return self.runtime_conf

    def get_dsl(self):
        return self.dsl

    def get_args_input(self):
        return self.args_input

    def get_need_deploy_parameter(self, name, deploy_cpns=None):
        if deploy_cpns is not None:
            return name in deploy_cpns

        return False

    def get_job_parameters(self, *args, **kwargs):
        return self.job_parameters

    def get_job_providers(self, provider_detail=None, dsl=None):
        if self.job_providers:
            return self.job_providers
        else:
            if dsl is None:
                self.job_providers = RuntimeConfParserUtil.get_job_providers(self.dsl, provider_detail)
            else:
                self.job_providers = RuntimeConfParserUtil.get_job_providers(dsl, provider_detail)
            return self.job_providers

    @staticmethod
    def _gen_predict_data_mapping():
        data_mapping = [("data", "data"), ("train_data", "test_data"),
                        ("validate_data", "test_data"), ("test_data", "test_data")]

        for data_key, data_value in data_mapping:
            yield data_key, data_value

    @staticmethod
    def generate_predict_conf_template(predict_dsl, train_conf, model_id, model_version):
        return RuntimeConfParserUtil.generate_predict_conf_template(predict_dsl,
                                                                    train_conf,
                                                                    model_id,
                                                                    model_version)

    @staticmethod
    def get_predict_dsl(predict_dsl=None, module_object_dict=None):
        if not predict_dsl:
            return {}

        role_predict_dsl = copy.deepcopy(predict_dsl)
        component_list = list(predict_dsl.get("components").keys())

        for component in component_list:
            module_object = module_object_dict.get(component)
            if module_object:
                role_predict_dsl["components"][component]["CodePath"] = module_object

        return role_predict_dsl

    @staticmethod
    def get_module_object_name(module, local_role, provider_detail,
                               provider_name, provider_version):
        if not provider_detail:
            raise ValueError("Component Providers should be provided")

        provider = RuntimeConfParserUtil.instantiate_component_provider(provider_detail,
                                                                        provider_name=provider_name,
                                                                        provider_version=provider_version)
        module_obj_name = RuntimeConfParserUtil.get_module_name(role=local_role,
                                                                module=module,
                                                                provider=provider)

        return module_obj_name

    @staticmethod
    def validate_component_param(component, module, runtime_conf,
                                 provider_name, provider_version, provider_detail,
                                 local_role, local_party_id):
        provider = RuntimeConfParserUtil.instantiate_component_provider(provider_detail,
                                                                        provider_name=provider_name,
                                                                        provider_version=provider_version)

        try:
            RuntimeConfParserUtil.get_component_parameters(provider,
                                                           runtime_conf,
                                                           module,
                                                           component,
                                                           redundant_param_check=True,
                                                           local_role=local_role,
                                                           local_party_id=local_party_id,
                                                           parse_user_specified_only=False)
            return 0
        except Exception as e:
            raise ValueError(f"{e}")

    @classmethod
    def check_input_existence(cls, dsl):
        component_details = dsl.get("components", {})
        component_outputs = cls._find_outputs(dsl)

        input_key = ["data", "model", "isometric_model", "cache"]
        non_existence = dict()
        for cpn, cpn_detail in component_details.items():
            for k in input_key:
                input_deps = cpn_detail.get("input", {}).get(k, {})
                if not input_deps:
                    continue

                input_splits = None
                if k == "data":
                    for data_k, dep_list in input_deps.items():
                        for dep in dep_list:
                            input_splits = dep.split(".", -1)

                else:
                    for dep in input_deps:
                        input_splits = dep.split(".", -1)
                        if input_splits[0] == "pipeline":
                            input_splits = input_splits[1:]

                up_cpn, up_link = input_splits
                if not component_outputs.get(up_cpn, {}).get(up_link, {}):
                    if k not in non_existence:
                        non_existence[k] = list()
                    non_existence[k].append(f"{cpn}'s {up_cpn}.{up_link}")

        if non_existence:
            ret_msg = "non exist input:"
            for k, v in non_existence.items():
                ret_msg += f"\n    {k}: " + ",".join(v)

            return ret_msg
        else:
            return ""


class DSLParserV1(BaseDSLParser):
    def __init__(self):
        super(DSLParserV1, self).__init__()
        self.version = 1

    @staticmethod
    def get_job_parameters(runtime_conf):
        job_parameters = RuntimeConfParserUtil.get_job_parameters(runtime_conf,
                                                                  conf_version=1)

        return job_parameters

    @staticmethod
    def parse_component_role_parameters(component, dsl, runtime_conf, provider_detail, provider_name,
                                        provider_version):
        provider = RuntimeConfParserUtil.instantiate_component_provider(provider_detail,
                                                                        provider_name=provider_name,
                                                                        provider_version=provider_version)

        role_parameters = RuntimeConfParserUtil.get_v1_role_parameters(provider,
                                                                       component,
                                                                       runtime_conf,
                                                                       dsl)

        return role_parameters

    @staticmethod
    def convert_dsl_v1_to_v2(dsl):
        dsl_v2 = copy.deepcopy(dsl)

        # change dsl v1 to dsl v2
        readers = {}
        ret_msg = []
        for cpn, cpn_detail in dsl["components"].items():
            new_cpn_detail = copy.deepcopy(cpn_detail)
            if cpn_detail.get("input", {}).get("data", {}):
                for data_key, dataset in cpn_detail["input"]["data"].items():
                    new_dataset = []
                    for data in dataset:
                        up_cpn, up_out_alias = data.split(".", -1)
                        if up_cpn == "args":
                            if up_out_alias not in readers:
                                readers[up_out_alias] = "_".join(["reader", str(len(readers))])
                                ret_msg.append(f"{data} is changed to {readers[up_out_alias]}.{up_out_alias}, please "
                                               f"set input data of {readers[up_out_alias]}")
                            up_link = ".".join([readers[up_out_alias], up_out_alias])
                            new_dataset.append(up_link)
                        else:
                            new_dataset.append(data)

                    new_cpn_detail["input"]["data"][data_key] = new_dataset

            dsl_v2["components"][cpn] = new_cpn_detail

        for output_alias, cpn in readers.items():
            reader_detail = dict(module="Reader",
                                 output={"data": [output_alias]},
                                 CodePath="Reader")
            dsl_v2["components"].update({cpn: reader_detail})

        return dsl_v2, ", ".join(ret_msg)

    @staticmethod
    def convert_conf_v1_to_v2(conf_v1, role_parameters):
        conf_v2 = dict()
        for attr, conf in conf_v1.items():
            if attr in ["algorithm_parameters", "role_parameters", "job_parameters"]:
                continue

            conf_v2[attr] = conf

        job_params = conf_v1.get("job_parameters", {})
        conf_v2["job_parameters"] = dict(common=job_params)

        algorithm_params = conf_v1.get("algorithm_parameters", {})
        if algorithm_params or conf_v1.get("role_parameters"):
            conf_v2["component_parameters"] = dict()
            if algorithm_params:
                conf_v2["component_parameters"]["common"] = algorithm_params

            if conf_v1.get("role_parameters"):
                conf_v2["component_parameters"]["role"] = dict()
                for cpn, role_params in role_parameters.items():
                    conf_v2["component_parameters"]["role"] = RuntimeConfParserUtil.merge_dict(conf_v2["component_parameters"]["role"],
                                                                                               role_params)

        conf_v2["dsl_version"] = 2

        return conf_v2

    """
    @staticmethod
    def change_conf_v1_to_v2(dsl_v2, conf_v1, provider_detail):
        # change conf v1 to conf v2
        readers = dict()
        for cpn, cpn_detail in dsl_v2["components"].items():
            if cpn_detail.get("module") != "Reader":
                continue

            output_alias = cpn_detail["output"]["data"]
            readers[output_alias] = cpn

        conf_v2 = RuntimeConfParserUtil.change_conf_v1_to_v2(dsl_v2, conf_v1, readers, provider_detail)
        return conf_v2
    """

    @staticmethod
    def get_components_light_weight(dsl_v2):
        components = []
        for cpn, cpn_detail in dsl_v2["components"].items():
            component = Component()
            component.set_name(cpn)
            component.set_module(cpn_detail["module"])
            components.append(component)

        return components


class DSLParserV2(BaseDSLParser):
    def __init__(self):
        super(DSLParserV2, self).__init__()
        self.version = 2

    def run(self, pipeline_runtime_conf=None, dsl=None, runtime_conf=None,
            provider_detail=None, mode="train",
            local_role=None, local_party_id=None, *args, **kwargs):

        if mode not in ["train", "predict"]:
            raise ModeError("")

        self.dsl = copy.deepcopy(dsl)
        self._init_components(mode, version=2)
        self._find_dependencies(mode, version=2)
        self.runtime_conf = runtime_conf
        self.pipeline_runtime_conf = pipeline_runtime_conf
        self.mode = mode
        self.local_role = local_role
        self.local_party_id = local_party_id

        if mode == "train":
            self.job_parameters = RuntimeConfParserUtil.get_job_parameters(self.runtime_conf,
                                                                           conf_version=2)

        else:
            predict_runtime_conf = RuntimeConfParserUtil.merge_predict_runtime_conf(pipeline_runtime_conf,
                                                                                    runtime_conf)
            self.predict_runtime_conf = predict_runtime_conf
            self.job_parameters = RuntimeConfParserUtil.get_job_parameters(predict_runtime_conf,
                                                                           conf_version=2)

        self.args_input = RuntimeConfParserUtil.get_input_parameters(runtime_conf,
                                                                     components=self._get_reader_components())

        self.prepare_graph_dependency_info()

        return self.components

    def parse_user_specified_component_parameters(self, component_name, provider_detail, provider_name,
                                                  provider_version, local_role, local_party_id, previous_parameters=None):
        if self.mode == "predict":
            runtime_conf = self.predict_runtime_conf
        else:
            runtime_conf = self.runtime_conf

        parameters = self._init_component_setting(component_name,
                                                  provider_detail,
                                                  provider_name,
                                                  provider_version,
                                                  local_role,
                                                  local_party_id,
                                                  runtime_conf,
                                                  redundant_param_check=False,
                                                  parse_user_specified_only=True,
                                                  previous_parameters=previous_parameters)

        return parameters

    def _get_reader_components(self):
        reader_components = []
        for cpn, conf in self.dsl.get("components").items():
            if conf.get("module") == "Reader":
                reader_components.append(cpn)

        return reader_components

    def get_source_connect_sub_graph(self, valid_nodes):
        invalid_nodes = set([self.components[i].get_name() for i in range(len(self.components))]) - set(valid_nodes)
        return self._get_source_connect_nodes(invalid_nodes)

    def get_need_revisit_nodes(self, visited_nodes, failed_nodes):
        invalid_nodes = set([self.components[i].get_name() for i in range(len(self.components))]) - set(visited_nodes)
        invalid_nodes |= set(failed_nodes)
        connected_nodes = self._get_source_connect_nodes(invalid_nodes)
        connected_nodes_name = [node.get_name() for node in connected_nodes]
        revisit_nodes = []
        for node in visited_nodes:
            if node not in connected_nodes_name:
                idx = self.component_name_index[node]
                revisit_nodes.append(self.components[idx])

        return revisit_nodes

    def _get_source_connect_nodes(self, invalid_nodes):
        in_degree = copy.deepcopy(self.in_degree)
        stack = []
        for i in range(len(self.components)):
            if self.components[i].get_name() in invalid_nodes:
                continue

            if in_degree[i] == 0:
                stack.append(i)

        connected_nodes = []
        while len(stack) > 0:
            idx = stack.pop()
            connected_nodes.append(self.components[idx])

            for down_name in self.component_downstream[idx]:
                if down_name in invalid_nodes:
                    continue
                down_idx = self.component_name_index.get(down_name)
                in_degree[down_idx] -= 1

                if in_degree[down_idx] == 0:
                    stack.append(down_idx)

        return connected_nodes

    @staticmethod
    def verify_conf_reusability(reused_conf, new_conf, reused_components):
        reused_components = set(reused_components)

        # step1: check role, it should be same
        # reused_conf_role = reused_conf.get("role", {})
        # new_conf_role = new_conf.get("role", {})
        # if reused_conf_role != new_conf_role:
        #     raise ValueError(f"role {reused_conf_role} does not equals to {new_conf_role}")

        # step2: check component common parameters
        pre_component_parameters = reused_conf.get("component_parameters", {})
        cur_component_parameters = new_conf.get("component_parameters", {})
        pre_common_params = pre_component_parameters.get("common", {})
        cur_common_params = cur_component_parameters.get("common", {})
        pre_role_params = pre_component_parameters.get("role", {})
        cur_role_params = cur_component_parameters.get("role", {})
        for cpn in reused_components:
            cpn_pre_common_params = pre_common_params.get(cpn, {})
            cpn_cur_common_params = cur_common_params.get(cpn, {})
            if cpn_pre_common_params != cpn_cur_common_params:
                raise ValueError(f"{cpn}'s common parameters old:{cpn_pre_common_params} != new:{cpn_cur_common_params}")

        # step3: check component role parameters
        first_role_params = pre_role_params
        second_role_params = cur_role_params
        for idx in range(2):
            for r, role_params in first_role_params.items():
                for party_idx, params in role_params.items():
                    for cpn in reused_components:
                        cpn_first_role_params = params.get(cpn)
                        if not cpn_first_role_params:
                            continue

                        cpn_second_role_params = second_role_params.get(r, {}).get(party_idx, {}).get(cpn)
                        if cpn_first_role_params != cpn_second_role_params:
                            if idx == 1:
                                cpn_first_role_params, cpn_second_role_params = cpn_second_role_params, cpn_first_role_params

                            raise ValueError(f"{cpn}'s role parameters old:{r}-{party_idx}-{cpn_first_role_params} "
                                             f"!= new: {r}-{party_idx}-{cpn_second_role_params}")

            first_role_params, second_role_params = cur_role_params, pre_role_params



