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
from fate_arch.common.base_utils import json_dumps, json_loads
from fate_flow.utils.object_utils import from_dict_hook
from fate_flow.entity.types import *
from fate_flow.entity import DataCache
from fate_arch.common import DTable


class TestType(unittest.TestCase):
    def test1(self):
        cache = DataCache(name="test_cache", data={"t1": DTable(namespace="test", name="test1")}, meta={"t1": {"a": 1}})
        a = json_loads(json_dumps(cache))
        self.assertEqual(a["data"]["t1"]["namespace"], "test")
        b = json_loads(json_dumps(cache, with_type=True), object_hook=from_dict_hook)
        self.assertEqual(b.data["t1"].namespace, "test")

    def test2(self):
        self.assertTrue(ComponentProviderName.valid("fate_flow"))
        self.assertFalse(ComponentProviderName.valid("fate_flow_xx"))
        self.assertTrue(ComponentProviderName("fate_flow") in ComponentProviderName)
        self.assertTrue(ComponentProviderName["FATE_FLOW"] in ComponentProviderName)
        self.assertTrue(ComponentProviderName("fate_flow") == ComponentProviderName.FATE_FLOW)
        self.assertTrue(ComponentProviderName("fate_flow") is ComponentProviderName.FATE_FLOW)
        print(ComponentProviderName.values())
        print(ComponentProviderName.FATE_FLOW)

        self.assertTrue(0 == KillProcessRetCode.KILLED)
        self.assertTrue(KillProcessRetCode.valid(0))
        self.assertFalse(KillProcessRetCode.valid(10))
        print(KillProcessRetCode.KILLED)


if __name__ == '__main__':
    unittest.main()
