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

import json
import pprint
import sys
from fate_flow.scheduler import dsl_parser

dsl_path_v1 = sys.argv[1]
conf_path_v1 = sys.argv[2]
provider_path = sys.argv[3]

"""test dsl v2"""
with open(dsl_path_v1, "r") as fin:
    dsl_v1 = json.loads(fin.read())

with open(conf_path_v1, "r") as fin:
    conf_v1 = json.loads(fin.read())

with open(provider_path, "r") as fin:
    provider_detail = json.loads(fin.read())


dsl_parser_v1 = dsl_parser.DSLParserV1()
dsl_v2, warning_msg = dsl_parser_v1.convert_dsl_v1_to_v2(dsl_v1)

pprint.pprint(dsl_v2)
print (warning_msg)
exit(0)
components = dsl_parser_v1.get_components_light_weight(dsl_v2)
for cpn in components:
    print (cpn.get_name())
    print (cpn.get_module())

pprint.pprint(dsl_parser_v1.get_job_parameters(conf_v1))

job_providers = dsl_parser_v1.get_job_providers(dsl=dsl_v2, provider_detail=provider_detail)
pprint.pprint(job_providers)
print("\n\n\n")

cpn_role_parameters = dict()
for cpn in components:
    cpn_name = cpn.get_name()
    role_params = dsl_parser_v1.parse_component_role_parameters(component=cpn_name,
                                                                dsl=dsl_v2,
                                                                runtime_conf=conf_v1,
                                                                provider_detail=provider_detail,
                                                                provider_name=job_providers[cpn_name]["provider"]["name"],
                                                                provider_version=job_providers[cpn_name]["provider"]["version"])

    print (cpn_name)
    pprint.pprint(role_params)
    print ("\n")

    cpn_role_parameters[cpn_name] = role_params

print ("\n\n\n")

conf_v2 = dsl_parser_v1.convert_conf_v1_to_v2(conf_v1, cpn_role_parameters)
pprint.pprint(conf_v2)
