#
#  Copyright 2022 The FATE Authors. All Rights Reserved.
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
from fate_flow.db.db_models import DB, PipelineComponentMeta


class PipelinedComponent:

    def __init__(self, model_id, model_version, role, party_id):
        self.model_id = model_id
        self.model_version = model_version
        self.role = role
        self.party_id = party_id

    @DB.connection_context()
    def read_define_meta(self):
        define_meta = {
            'component_define': {},
            'model_proto': {},
        }

        query = PipelineComponentMeta.select().where(
            PipelineComponentMeta.f_model_id == self.model_id,
            PipelineComponentMeta.f_model_version == self.model_version,
            PipelineComponentMeta.f_role == self.role,
            PipelineComponentMeta.f_party_id == self.party_id,
        )

        for row in query:
            define_meta['component_define'][row.f_component_name] = {
                'module_name': row.f_component_module_name,
            }
            define_meta['model_proto'][row.f_component_name] = {
                row.f_model_alias: row.f_model_proto_index,
            }

        return define_meta

    @DB.connection_context()
    def write_define_meta(self, component_name, component_module_name, model_alias, model_proto_index):
        return PipelineComponentMeta.create(
            f_model_id=self.model_id,
            f_model_version=self.model_version,
            f_role=self.role,
            f_party_id=self.party_id,
            f_component_name=component_name,
            f_component_module_name=component_module_name,
            f_model_alias=model_alias,
            f_model_proto_index=model_proto_index,
        )
