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
from fate_flow.entity.types import OutputCache
from fate_arch.common import DTable
from fate_arch.common.base_utils import json_dumps, json_loads
from fate_flow.utils.object_utils import from_dict_hook


class TestType(unittest.TestCase):
    def test1(self):
        cache = OutputCache(data={"t1": DTable(namespace="test", name="test1")}, meta={"t1": {"a": 1}})
        a = json_loads(json_dumps(cache))
        self.assertEqual(a["data"]["t1"]["namespace"], "test")
        b = json_loads(json_dumps(cache, with_type=True), object_hook=from_dict_hook)
        self.assertEqual(b.data["t1"].namespace, "test")


if __name__ == '__main__':
    unittest.main()
