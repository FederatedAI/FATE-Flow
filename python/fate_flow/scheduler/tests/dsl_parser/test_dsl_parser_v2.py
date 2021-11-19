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
import json
import pprint
import sys
from fate_flow.scheduler import dsl_parser

"""
def run(self, pipeline_dsl=None, pipeline_runtime_conf=None, dsl=None, runtime_conf=None,
        provider_detail=None, mode="train", local_role=None,
        local_party_id=None, deploy_detail=None, *args, **kwargs):
"""

dsl_path_v2 = sys.argv[1]
conf_path_v2 = sys.argv[2]
provider_path = sys.argv[3]

"""test dsl v2"""
with open(dsl_path_v2, "r") as fin:
    dsl_v2 = json.loads(fin.read())

with open(conf_path_v2, "r") as fin:
    conf_v2 = json.loads(fin.read())

with open(provider_path, "r") as fin:
    provider_detail = json.loads(fin.read())

dsl_parser_v2 = dsl_parser.DSLParserV2()
dsl_parser_v2.run(dsl=dsl_v2,
                  runtime_conf=conf_v2,
                  mode="train")

pprint.pprint(dsl_parser_v2.get_job_parameters())
print("\n\n\n")
pprint.pprint(dsl_parser_v2.get_job_providers(provider_detail=provider_detail))

print("\n\n\n")
pprint.pprint(dsl_parser_v2.get_dependency())
pprint.pprint(dsl_parser_v2.get_dsl_hierarchical_structure())
print("\n\n\n")

job_providers = dsl_parser_v2.get_job_providers(provider_detail=provider_detail)

component_parameters = dict()
for component in job_providers.keys():
    provider_info = job_providers[component]["provider"]
    provider_name = provider_info["name"]
    provider_version = provider_info["version"]

    parameter = dsl_parser_v2.parse_component_parameters(component,
                                                         provider_detail,
                                                         provider_name,
                                                         provider_version,
                                                         local_role="guest",
                                                         local_party_id=10000)

    user_parameter = dsl_parser_v2.parse_user_specified_component_parameters(component,
                                                                             provider_detail,
                                                                             provider_name,
                                                                             provider_version,
                                                                             local_role="guest",
                                                                             local_party_id=10000)

    component_parameters[component] = parameter
    # pprint.pprint(component)
    # pprint.pprint(parameter)

    pprint.pprint(user_parameter)
    print("\n\n\n")

evaluation_paramters = {'CodePath': 'Evaluation',
                        'ComponentParam': {'eval_type': 'multi', "test": "test_keyword"},
                        'dsl_version': 2,
                        'initiator': {'party_id': 10000, 'role': 'guest'},
                        'job_parameters': {'common': {'backend': 0,
                                                      'job_type': 'train',
                                                      'work_mode': 1}},
                        'local': {'party_id': 10000, 'role': 'guest'},
                        'module': 'Evaluation',
                        'role': {'arbiter': [9999], 'guest': [10000], 'host': [9999]}}

provider_info = job_providers["evaluation_0"]["provider"]
provider_name = provider_info["name"]
provider_version = provider_info["version"]

new_evaluation_parameter = dsl_parser_v2.parse_component_parameters("evaluation_0",
                                                                    provider_detail,
                                                                    provider_name,
                                                                    provider_version,
                                                                    local_role="guest",
                                                                    local_party_id=10000,
                                                                    previous_parameters={"evaluation_0": evaluation_paramters})

pprint.pprint(new_evaluation_parameter)
pprint.pprint(dsl_parser_v2.get_dependency_with_parameters(component_parameters))
print("\n\n\n")

print(dsl_parser_v2.get_dsl_hierarchical_structure())
print(dsl_parser_v2.get_dsl_hierarchical_structure()[0]["reader_0"].get_component_provider())
print("\n\n\n")

pprint.pprint(dsl_parser_v2.deploy_component(["reader_0", "dataio_0"], dsl_v2))
print("\n\n\n")

module_object_name_mapping = dict()
for component in job_providers.keys():
    module = dsl_v2["components"][component]["module"]
    provider_info = job_providers[component]["provider"]
    provider_name = provider_info["name"]
    provider_version = provider_info["version"]
    module_object = dsl_parser_v2.get_module_object_name(module, "guest", provider_detail,
                                                         provider_name, provider_version)

    module_object_name_mapping[component] = module_object

pprint.pprint(dsl_parser_v2.get_predict_dsl(dsl_v2, module_object_name_mapping))
print(dsl_parser_v2.get_downstream_dependent_components("dataio_0"))
print(dsl_parser_v2.get_upstream_dependent_components("dataio_0"))


dsl = copy.deepcopy(dsl_v2)
del dsl["components"]["reader_0"]
del dsl["components"]["dataio_0"]
del dsl["components"]["hetero_feature_selection_0"]

print(dsl_parser_v2.check_input_existence(dsl))
print("\n\n\n")

conf_v2["component_parameters"]["common"]["evaluation_0"]["test"] = "test"
provider_info = job_providers["evaluation_0"]["provider"]
provider_name = provider_info["name"]
provider_version = provider_info["version"]

try:
    dsl_parser_v2.validate_component_param(component="evaluation_0",
                                           module="Evaluation",
                                           runtime_conf=conf_v2,
                                           provider_name=provider_name,
                                           provider_version=provider_version,
                                           provider_detail=provider_detail,
                                           local_role="guest",
                                           local_party_id=10000)
except Exception as e:
    print (e)




