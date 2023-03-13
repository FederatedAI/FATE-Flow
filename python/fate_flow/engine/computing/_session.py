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
from fate_flow.engine.computing._eggroll import ContainerdEggrollEngine, LocalEggrollEngine
from fate_flow.engine.computing._spark import SparkEngine
from fate_flow.entity.types import ComputingEngine, EngineType, ProviderDevice
from fate_flow.manager.provider_manager import ProviderManager
from fate_flow.runtime.component_provider import ComponentProvider
from fate_flow.runtime.system_settings import ENGINES


def build_engine(provider_name: str):
    provider = ProviderManager.get_provider_by_provider_name(provider_name)
    computing_engine = ENGINES.get(EngineType.COMPUTING)
    if computing_engine in {ComputingEngine.EGGROLL, ComputingEngine.STANDALONE}:
        if ComponentProvider.device in {ProviderDevice.DOCKER, ProviderDevice.K8S}:
            engine_session = ContainerdEggrollEngine(provider)
        else:
            engine_session = LocalEggrollEngine(provider)
    elif computing_engine == ComputingEngine.SPARK:
        engine_session = SparkEngine(provider)
    else:
        raise ValueError(f'engine "{computing_engine}" is not supported')
    return engine_session
