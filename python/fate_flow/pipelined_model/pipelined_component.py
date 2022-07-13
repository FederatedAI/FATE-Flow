#
#  Copyright 2022 The FATE Authors. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the 'License');
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an 'AS IS' BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
import shutil
from pathlib import Path

from fate_arch.common.base_utils import current_timestamp

from fate_flow.db.db_models import DB, PipelineComponentMeta
from fate_flow.model import Locker
from fate_flow.utils.base_utils import get_fate_flow_directory
from fate_flow.utils.model_utils import gen_party_model_id


class PipelinedComponent(Locker):

    def __init__(self, role, party_id, model_id, model_version):
        self.role = role
        self.party_id = party_id
        self.model_id = model_id
        self.party_model_id = gen_party_model_id(model_id, role, party_id)
        self.model_version = model_version

        self.model_path = get_fate_flow_directory('model_local_cache', model_id, model_version)
        self.variables_index_path = Path(self.model_path, 'variables', 'index')
        self.variables_data_path = Path(self.model_path, 'variables', 'data')
        self.run_parameters_path = Path(self.model_path, 'run_parameters')
        self.checkpoint_path = Path(self.model_path, 'checkpoint')

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
            f_create_time=current_timestamp(),
            f_model_id=self.model_id,
            f_model_version=self.model_version,
            f_role=self.role,
            f_party_id=self.party_id,
            f_component_name=component_name,
            f_component_module_name=component_module_name,
            f_model_alias=model_alias,
            f_model_proto_index=model_proto_index,
        )

    def pack_component(self):
        shutil.copy2
        return define_meta['component_define']
