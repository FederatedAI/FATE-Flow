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
from fate_flow.db.db_models import DB, CacheTracking
from fate_flow.utils import base_utils
from fate_flow.entity.types import OutputCache
from fate_arch.common.base_utils import current_timestamp


class CacheManager:
    @classmethod
    @DB.connection_context()
    def save_tracking(cls, cache: OutputCache, job_id, component_name, task_id: str = None, task_version: int = None, cache_name: str = None):
        tracking = CacheTracking()
        tracking.f_create_time = current_timestamp()
        tracking.f_cache_key = cls.generate_cache_key(task_id, task_version, cache_name)
        tracking.f_cache = cache
        tracking.f_job_id = job_id
        tracking.f_component_name = component_name
        tracking.f_task_id = task_id
        tracking.f_task_version = task_version
        tracking.f_cache_name = cache_name
        rows = tracking.save(force_insert=True)
        if rows != 1:
            raise Exception("save cache tracking failed")
        return tracking.f_cache_key

    @classmethod
    @DB.connection_context()
    def query_tracking(cls, cache_key: str = None, task_id: str = None, task_version: int = None, cache_name: str = None, **kwargs):
        trackings = CacheTracking.query(cache_key=cache_key, task_id=task_id, task_version=task_version, cache_name=cache_name, **kwargs)
        return [tracking.f_cache for tracking in trackings]

    @classmethod
    def generate_cache_key(cls, task_id: str = None, task_version: int = None, cache_name: str = None):
        if task_id and task_version and cache_name:
            return "-".join([task_id, str(task_version), cache_name])
        else:
            return base_utils.new_unique_id()
