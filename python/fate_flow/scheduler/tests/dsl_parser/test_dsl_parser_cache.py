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

dsl_path = sys.argv[1]
conf_path = sys.argv[2]
provider_path = sys.argv[3]

with open(dsl_path, "r") as fin:
    dsl = json.loads(fin.read())

with open(conf_path, "r") as fin:
    conf = json.loads(fin.read())

with open(provider_path, "r") as fin:
    provider_detail = json.loads(fin.read())


dsl_parser_v2 = dsl_parser.DSLParserV2()
dsl_parser_v2.run(dsl=dsl,
                  runtime_conf=conf,
                  mode="train")

pprint.pprint(dsl_parser_v2.get_job_parameters())
print ("\n\n\n")
pprint.pprint(dsl_parser_v2.get_job_providers(provider_detail=provider_detail,
                                              local_role="arbiter",
                                              local_party_id=9999))
print ("\n\n\n")
pprint.pprint(dsl_parser_v2.get_dependency())
print ("\n\n\n")

job_providers = dsl_parser_v2.get_job_providers(provider_detail=provider_detail,
                                                local_role="arbiter",
                                                local_party_id=9999)
component_parameters = dict()
for component in job_providers.keys():
    provider_info = job_providers[component]["provider"]
    provider_name = provider_info["name"]
    provider_version = provider_info["version"]

    parameter = dsl_parser_v2.parse_component_parameters(component,
                                                         provider_detail,
                                                         provider_name,
                                                         provider_version,
                                                         local_role="arbiter",
                                                         local_party_id=9999)

    component_parameters[component] = parameter
    pprint.pprint (parameter)

pprint.pprint(dsl_parser_v2.get_dependency_with_parameters(component_parameters))
print ("\n\n\n")


pprint.pprint(dsl_parser_v2.deploy_component(["reader_0", "dataio_0", "intersection_0"], dsl))
print ("\n\n\n")

pprint.pprint(dsl_parser_v2.deploy_component(["reader_0", "dataio_0", "intersection_1"], dsl))
print ("\n\n\n")

pprint.pprint(dsl_parser_v2.deploy_component(["reader_0", "dataio_0", "intersection_0", "intersection_1"], dsl))
print ("\n\n\n")
