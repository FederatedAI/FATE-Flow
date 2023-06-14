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
from fate_flow.entity.spec import DAGSchema
from fate_flow.entity.types import ProviderName, ProviderDevice
from fate_flow.runtime.component_provider import ComponentProvider


class FlowHub:
    @staticmethod
    def load_job_parser(dag):
        if isinstance(dag, DAGSchema):
            from fate_flow.hub.parser.default import JobParser
            return JobParser(dag)

    @staticmethod
    def load_job_scheduler():
        from fate_flow.hub.scheduler.default import DAGScheduler
        return DAGScheduler()

    @staticmethod
    def load_provider_entrypoint(provider: ComponentProvider):
        entrypoint = None
        if provider.name == ProviderName.FATE and provider.device == ProviderDevice.LOCAL:
            from fate_flow.hub.provider.fate import LocalFateEntrypoint
            entrypoint = LocalFateEntrypoint(provider)
        return entrypoint

    @staticmethod
    def load_components_wraps(config, name="default"):
        if name == "default":
            from fate_flow.hub.components_wraps.default import FlowWraps
            return FlowWraps(config)
