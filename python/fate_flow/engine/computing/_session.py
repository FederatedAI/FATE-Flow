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
from fate.arch.common import EngineType
from fate_flow.engine.computing._eggroll import EggrollEngine
from fate_flow.engine.computing._spark import SparkEngine
from fate_flow.entity.engine_types import ComputingEngine
from fate_flow.settings import ENGINES


def build_engine(computing_engine=None):
    if not computing_engine:
        computing_engine = ENGINES.get(EngineType.COMPUTING)
    if computing_engine in {ComputingEngine.EGGROLL, ComputingEngine.STANDALONE}:
        engine_session = EggrollEngine()
    elif computing_engine == ComputingEngine.SPARK:
        engine_session = SparkEngine()
    else:
        raise ValueError(f"{computing_engine} is not supported")
    return engine_session
