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
from fate_flow.engine.devices._base import EngineABC
from fate_flow.entity.types import ProviderDevice, LauncherType
from fate_flow.manager.service.provider_manager import ProviderManager


def build_engine(provider_name: str, launcher_name: str = LauncherType.DEFAULT):
    provider = ProviderManager.get_provider_by_provider_name(provider_name)

    if launcher_name == LauncherType.DEEPSPEED:
        if provider.device in {ProviderDevice.LOCAL}:
            from fate_flow.engine.devices.deepspeed import EggrollDeepspeedEngine
            engine_session = EggrollDeepspeedEngine(provider)
        else:
            raise ValueError(f'engine launcher {LauncherType.DEEPSPEED} device "{provider.device}" is not supported')

    else:
        if provider.device in {ProviderDevice.DOCKER, ProviderDevice.K8S}:
            from fate_flow.engine.devices.container import ContainerdEngine
            engine_session = ContainerdEngine(provider)

        elif provider.device in {ProviderDevice.LOCAL}:
            from fate_flow.engine.devices.local import LocalEngine
            engine_session = LocalEngine(provider)

        else:
            raise ValueError(f'engine device "{provider.device}" is not supported')

    return engine_session
