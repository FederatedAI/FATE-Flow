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
from fate_flow.utils.log_utils import getLogger
from fate_flow.components._base import (
    BaseParam,
    ComponentBase,
    ComponentMeta,
    ComponentInputProtocol,
)
from fate_flow.operation.job_tracker import Tracker
from fate_flow.entity import MetricMeta

LOGGER = getLogger()

cache_loader_cpn_meta = ComponentMeta("CacheLoader")


@cache_loader_cpn_meta.bind_param
class CacheLoaderParam(BaseParam):
    def __init__(self, cache_key=None, job_id=None, component_name=None, cache_name=None):
        super().__init__()
        self.cache_key = cache_key
        self.job_id = job_id
        self.component_name = component_name
        self.cache_name = cache_name

    def check(self):
        return True


@cache_loader_cpn_meta.bind_runner.on_guest.on_host
class CacheLoader(ComponentBase):
    def __init__(self):
        super(CacheLoader, self).__init__()
        self.parameters = {}
        self.cache_key = None
        self.job_id = None
        self.component_name = None
        self.cache_name = None

    def _run(self, cpn_input: ComponentInputProtocol):
        self.parameters = cpn_input.parameters
        LOGGER.info(self.parameters)
        for k, v in self.parameters.items():
            if hasattr(self, k):
                setattr(self, k, v)
        tracker = Tracker(job_id=self.job_id,
                          role=self.tracker.role,
                          party_id=self.tracker.party_id,
                          component_name=self.component_name)
        LOGGER.info(f"query cache by cache key: {self.cache_key} cache name: {self.cache_name}")
        # todo: use tracker client but not tracker
        caches = tracker.query_output_cache(cache_key=self.cache_key, cache_name=self.cache_name)
        if not caches:
            raise Exception("can not found this cache")
        elif len(caches) > 1:
            raise Exception(f"found {len(caches)} caches, only support one, please check parameters")
        else:
            cache = caches[0]
            self.cache_output = cache
            tracker.job_id = self.tracker.job_id
            tracker.component_name = self.tracker.component_name
            metric_meta = cache.to_dict()
            metric_meta.pop("data")
            metric_meta["component_name"] = self.component_name
            self.tracker.set_metric_meta(metric_namespace="cache_loader", metric_name=cache.name, metric_meta=MetricMeta(name="cache", metric_type="cache_info", extra_metas=metric_meta))
