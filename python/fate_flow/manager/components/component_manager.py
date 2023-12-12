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


from fate_flow.controller.job import JobController
from fate_flow.entity.code import ReturnCode
from fate_flow.entity.spec.dag import PartyTaskRefSpec, TaskSpec, PartySpec, RuntimeInputArtifacts, \
    RuntimeTaskOutputChannelSpec
from fate_flow.entity.types import EngineType
from fate_flow.manager.components.base import Base
from fate_flow.manager.service.provider_manager import ProviderManager
from fate_flow.runtime.system_settings import ENGINES, STORAGE, TEMP_DIR
from fate_flow.engine import storage
from fate_flow.errors.server_error import ExistsTable
from fate_flow.utils.file_utils import save_file


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
        result = JobController.request_create_job(dag_schema, is_local=True)
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
        result = JobController.request_create_job(dag_schema, is_local=True)
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
        result = JobController.request_create_job(dag_schema, is_local=True)
        if result.get("code") == ReturnCode.Base.SUCCESS:
            result["data"] = {"name": name, "namespace": namespace, "path": path}
        return result

    @classmethod
    def upload_dataframe(cls, file, head, partitions, meta, namespace, name, extend_sid, is_temp_file=False):
        parameters = {
            "file": file,
            "head": head,
            "partitions": partitions,
            "meta": meta,
            "extend_sid": extend_sid,
            "is_temp_file": is_temp_file
        }
        address = STORAGE.get(ENGINES.get(EngineType.STORAGE))
        if address:
            parameters.update({"address": address})
        role = "local"
        party_id = "0"
        upload_name = "upload_0"
        upload_ref = "upload"
        transformer_name = "transformer_0"
        transformer_ref = "dataframe_transformer"

        dag_schema = cls.local_dag_schema(
            task_name=upload_name,
            component_ref=upload_ref,
            parameters=parameters,
            role=role,
            party_id=party_id
        )
        dag_schema.dag.party_tasks[f"{role}_{party_id}"].tasks[transformer_name] = PartyTaskRefSpec(
            parameters={"namespace": namespace, "name": name}
        )

        fate_provider = ProviderManager.get_default_fate_provider()

        dag_schema.dag.tasks[transformer_name] = TaskSpec(
            component_ref=transformer_ref,
            parties=[PartySpec(role=role, party_id=[party_id])],
            conf=dict({"provider": fate_provider.provider_name}),
            inputs=RuntimeInputArtifacts(
                data={
                    "table": {
                        "task_output_artifact":
                            RuntimeTaskOutputChannelSpec(producer_task=upload_name, output_artifact_key="table")}
                })
        )
        result = JobController.request_create_job(dag_schema, is_local=True)
        if result.get("code") == ReturnCode.Base.SUCCESS:
            result["data"] = {"name": name, "namespace": namespace}
        return result

    @classmethod
    def upload_file(cls, file, head, partitions, meta, namespace, name, extend_sid):
        os.makedirs(TEMP_DIR, exist_ok=True)
        with NamedTemporaryFile(dir=TEMP_DIR, delete=False) as temp_file:
            temp_path = temp_file.name
            save_file(file, temp_path)
        return cls.upload_dataframe(temp_path, head, partitions, meta, namespace, name, extend_sid, is_temp_file=True)
