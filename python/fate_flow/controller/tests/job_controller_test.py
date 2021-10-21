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
import unittest

from fate_flow.utils.base_utils import jprint
from fate_flow.controller.job_controller import JobController
from fate_flow.utils import job_utils


class TestJobController(unittest.TestCase):
    def test_gen_updated_parameters(self):
        job_id = "202110211127411105150"
        initiator_role = "guest"
        initiator_party_id = 9999
        input_job_parameters = {
            "common": {
                "auto_retries": 1,
                "auto_retry_delay": 1
            }
        }
        input_job_parameters = {}
        input_component_parameters = {
            "common": {
                "hetero_lr_0": {
                    "alpha": 0.02
                }
            },
            "role": {
                "guest": {
                    "0": {
                        "reader_0": {
                            "table": {"name": "breast_hetero_guest", "namespace": "unitest_experiment"}
                        },
                        "homo_nn_0":{
                            "with_label": True,
                            "output_format": "dense"
                        },
                    }
                },
                "host": {
                    "1": {
                        "dataio_0":{
                            "with_label": True,
                            "output_format": "dense"
                        },
                        "evaluation_0": {
                            "need_run": True
                        }
                    }
                }
            }
        }
        job_configuration = job_utils.get_job_configuration(job_id=job_id,
                                                            role=initiator_role,
                                                            party_id=initiator_party_id)
        origin_job_parameters = job_configuration.runtime_conf["job_parameters"]
        origin_component_parameters = job_configuration.runtime_conf["component_parameters"]

        updated_job_parameters, updated_component_parameters, updated_components = JobController.gen_updated_parameters(
            job_id=job_id,
            initiator_role=initiator_role,
            initiator_party_id=initiator_party_id,
            input_job_parameters=input_job_parameters,
            input_component_parameters=input_component_parameters)
        jprint(updated_job_parameters)
        jprint(updated_component_parameters)
        self.assertTrue(check(input_component_parameters, updated_component_parameters)[0])
        # todo: add check with origin parameters and add dsl parser check


def check(inputs, result):
    # todo: return check keys chain
    if type(result) != type(inputs):
        return False, "type not match"
    elif isinstance(inputs, dict):
        for k, v in inputs.items():
            if k not in result:
                return False, f"no such {k} key"
            if isinstance(v, (dict, list)):
                return check(v, result[k])
            else:
                if result[k] != v:
                    return False, f"{k} value not match"
                else:
                    return True, "match"
    elif isinstance(inputs, list):
        return result == inputs
    else:
        raise Exception(f"not support type {type(inputs)}")


if __name__ == '__main__':
    unittest.main()
