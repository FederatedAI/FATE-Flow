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
from fate_flow.entity import JobConfigurationBase, JobConfiguration


class TestJobConfiguration(unittest.TestCase):
    def test(self):
        self.assertEqual(JobConfigurationBase(**{"runtime_conf": {"conf": 0}, "dsl": {"dsl"}}).runtime_conf.get("conf"), 0)
        self.assertEqual(JobConfigurationBase(**{"job_runtime_conf": {"conf": 0}, "job_dsl": {"dsl"}}).runtime_conf.get("conf"), 0)
        self.assertEqual(JobConfiguration(**{"runtime_conf": {"conf": 0}, "dsl": {"dsl"}, "runtime_conf_on_party": {"conf": 2}, "train_runtime_conf": {"conf": 2}}).runtime_conf.get("conf"), 0)
        self.assertEqual(JobConfiguration(**{"runtime_conf": {"conf": 0}, "dsl": {"dsl"}, "runtime_conf_on_party": {"conf": 2}, "train_runtime_conf": {"conf": 2}}).runtime_conf_on_party.get("conf"), 2)


if __name__ == '__main__':
    unittest.main()
