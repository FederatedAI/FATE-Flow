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
import uuid
import os
from tempfile import NamedTemporaryFile
import concurrent.futures

from fate_flow.controller.job import JobController
from fate_flow.entity.code import ReturnCode
from fate_flow.entity.types import EngineType
from fate_flow.manager.components.base import Base
from fate_flow.manager.service.provider_manager import ProviderManager
from fate_flow.runtime.system_settings import ENGINES, STORAGE
from fate_flow.engine import storage
from fate_flow.errors.server_error import ExistsTable
from fate_flow.utils.file_utils import save_file
from fate_flow.utils.file_utils import get_fate_flow_directory


class ComponentManager(Base):
    @classmethod
    def upload(cls, file, head, partitions, meta, namespace, name, extend_sid, temp_path=None):
        parameters = {
            "file": file,
            "head": head,
            "partitions": partitions,
            "meta": meta,
            "extend_sid": extend_sid,
            "is_temp_file": True if temp_path else False
        }
        if not name or not namespace:
            name = str(uuid.uuid1())
            namespace = "upload"
        parameters.update({
            "storage_engine": ENGINES.get(EngineType.STORAGE),
            "name": name,
            "namespace": namespace
        })
        address = STORAGE.get(ENGINES.get(EngineType.STORAGE))
        if address:
            parameters.update({"address": address})
        dag_schema = cls.local_dag_schema(
            task_name="upload_0",
            component_ref="upload",
            parameters=parameters
        )
        result = JobController.request_create_job(dag_schema.dict(), is_local=True)
        if result.get("code") == ReturnCode.Base.SUCCESS:
            result["data"] = {"name": name, "namespace": namespace}
        return result

    @classmethod
    def dataframe_transformer(cls, data_warehouse, namespace, name, drop, site_name):
        data_table_meta = storage.StorageTableMeta(name=name, namespace=namespace)
        if data_table_meta:
            if not drop:
                raise ExistsTable(
                    name=name,
                    namespace=namespace,
                    warning="If you want to ignore this error and continue transformer, "
                            "you can set the parameter of 'drop' to 'true' "
                )
            data_table_meta.destroy_metas()
        provider = ProviderManager.get_default_fate_provider()
        dag_schema = cls.local_dag_schema(
            task_name="transformer_0",
            component_ref="dataframe_transformer",
            parameters={"namespace": namespace, "name": name, "site_name": site_name},
            inputs={"data": {"table": {"data_warehouse": data_warehouse}}},
            provider=provider
        )
        result = JobController.request_create_job(dag_schema.dict(), is_local=True)
        if result.get("code") == ReturnCode.Base.SUCCESS:
            result["data"] = {"name": name, "namespace": namespace}
        return result

    @classmethod
    def download(cls, namespace, name, path):
        dag_schema = cls.local_dag_schema(
            task_name="download_0",
            component_ref="download",
            parameters=dict(namespace=namespace, name=name, path=path)
        )
        result = JobController.request_create_job(dag_schema.dict(), is_local=True)
        if result.get("code") == ReturnCode.Base.SUCCESS:
            result["data"] = {"name": name, "namespace": namespace, "path": path}
        return result

    @classmethod
    def upload_file(cls, file, head, partitions, meta, namespace, name, extend_sid):
        path = os.path.join(get_fate_flow_directory(), "temp_file")
        with NamedTemporaryFile(dir=path, prefix='temp_file_', suffix='.csv', delete=False) as temp_file:
            temp_path = temp_file.name
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                future = executor.submit(save_file, file, temp_path)
                # future.result()

        return cls.upload(temp_path, head, partitions, meta, namespace, name, extend_sid, temp_path=temp_path)

