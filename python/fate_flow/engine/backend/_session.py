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
from fate_flow.engine.backend._eggroll import EggrollEngine
from fate_flow.engine.backend._spark import SparkEngine
from fate_flow.entity.types import ComputingEngine


def build_backend(backend_name: str):
    if backend_name in {ComputingEngine.EGGROLL, ComputingEngine.STANDALONE}:
        backend = EggrollEngine()
    elif backend_name == ComputingEngine.SPARK:
        backend = SparkEngine()
    else:
        raise ValueError(f'backend "{backend_name}" is not supported')
    return backend
