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
import os

from fate_flow.db.db_models import DependenciesStorageMeta, DB
from fate_flow.entity.types import FateDependenceStorageEngine


class DependenceRegistry:
    @classmethod
    @DB.connection_context()
    def get_dependencies_storage_meta(cls, get_or_one=False, **kwargs):
        kwargs["storage_engine"] = FateDependenceStorageEngine.HDFS.value
        dependencies_storage_info = DependenciesStorageMeta.query(**kwargs)
        if get_or_one:
            return dependencies_storage_info[0] if dependencies_storage_info else None
        return dependencies_storage_info

    @classmethod
    @DB.connection_context()
    def save_dependencies_storage_meta(cls, storage_meta, status_check=False):
        entity_model, status = DependenciesStorageMeta.get_or_create(
            f_storage_engine=storage_meta.get("f_storage_engine"),
            f_type=storage_meta.get("f_type"),
            f_version=storage_meta.get("f_version"),
            defaults=storage_meta)
        if status is False:
            if status_check:
                if "f_upload_status" in storage_meta.keys() and storage_meta["f_upload_status"] \
                        != entity_model.f_upload_status:
                    return
            for key in storage_meta:
                setattr(entity_model, key, storage_meta[key])
            entity_model.save(force_insert=False)

    @classmethod
    def get_modify_time(cls, path):
        return int(os.path.getmtime(path)*1000)


