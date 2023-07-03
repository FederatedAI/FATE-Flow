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

from fate_flow.controller.job_controller import JobController
from fate_flow.entity.code import ReturnCode
from fate_flow.entity.types import EngineType
from fate_flow.manager.components.base import Base
from fate_flow.manager.service.provider_manager import ProviderManager
from fate_flow.runtime.system_settings import ENGINES


class ComponentManager(Base):
    @classmethod
    def upload(cls, file, head, partitions, meta, namespace, name, extend_sid):
        parameters = {
            "file": file,
            "head": head,
            "partitions": partitions,
            "meta": meta,
            "extend_sid": extend_sid
        }
        if not name or not namespace:
            name = str(uuid.uuid1())
            namespace = "upload"
        parameters.update({
            "storage_engine": ENGINES.get(EngineType.STORAGE),
            "name": name,
            "namespace": namespace
        })

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
    def dataframe_transformer(cls, data_warehouse, namespace, name):
        provider = ProviderManager.get_default_fate_provider()
        dag_schema = cls.local_dag_schema(
            task_name="transformer_0",
            component_ref="dataframe_transformer",
            parameters={"namespace": namespace, "name": name},
            inputs={"data": {"table": {"data_warehouse": data_warehouse}}},
            provider=provider
        )
        result = JobController.request_create_job(dag_schema.dict(), is_local=True)
        if result.get("code") == ReturnCode.Base.SUCCESS:
            result["data"] = {"name": name, "namespace": namespace}
        return result