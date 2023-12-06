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
from fate_flow.engine.backend._eggroll_deepspeed import Deepspeed
from fate_flow.entity.types import ComputingEngine, LauncherType


def build_backend(backend_name: str, launcher_name: str = LauncherType.DEFAULT):
    if backend_name in {ComputingEngine.EGGROLL, ComputingEngine.STANDALONE}:
        if launcher_name == LauncherType.DEEPSPEED:
            backend = Deepspeed()
        elif not launcher_name or launcher_name == LauncherType.DEFAULT:
            backend = EggrollEngine()
        else:
            raise ValueError(f'backend "{backend_name}" launcher {launcher_name} is not supported')
    elif backend_name == ComputingEngine.SPARK:
        backend = SparkEngine()
    else:
        raise ValueError(f'backend "{backend_name}" is not supported')
    return backend
