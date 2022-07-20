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
import hashlib
from pathlib import Path
from zipfile import ZipFile

from fate_arch.common.base_utils import current_timestamp

from fate_flow.db.db_models import DB, PipelineComponentMeta
from fate_flow.model import Locker
from fate_flow.settings import TEMP_DIRECTORY
from fate_flow.utils.base_utils import get_fate_flow_directory


class PipelinedComponent(Locker):

    def __init__(self, *, role=None, party_id=None, model_id=None, party_model_id=None, model_version):
        if party_model_id is None:
            self.role = role
            self.party_id = party_id
            self.model_id = model_id
            self.party_model_id = f'{role}#{party_id}#{model_id}'
        else:
            self.role, self.party_id, self.model_id = party_model_id.split('#', 2)
            self.party_model_id = party_model_id

        self.model_version = model_version

        self.model_path = get_fate_flow_directory('model_local_cache', self.model_id, self.model_version)
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

    def walk_component(self, zip_file, dir_path: Path):
        for path in dir_path.iterdir():
            if path.is_dir():
                self.walk_component(zip_file, path)
            else:
                zip_file.write(path, path.relative_to(self.model_path))

    def pack_component(self, component_name):
        filename = Path(TEMP_DIRECTORY, f'{self.party_model_id}_{self.model_version}_{component_name}.zip')

        with self.lock:
            with ZipFile(filename, 'w') as zip_file:
                self.walk_component(zip_file, self.variables_index_path / component_name)
                self.walk_component(zip_file, self.variables_data_path / component_name)
                self.walk_component(zip_file, self.run_parameters_path / component_name)
                self.walk_component(zip_file, self.checkpoint_path / component_name)

            with open(filename, 'rb') as f:
                hash_ = hashlib.sha256(f.read()).hexdigest()

        return filename, hash_

    def unpack_component(self, component_name, hash_=None):
        filename = Path(TEMP_DIRECTORY, f'{self.party_model_id}_{self.model_version}_{component_name}.zip')

        with self.lock:
            if hash_ is not None:
                with open(filename, 'rb') as f:
                    sha256 = hashlib.sha256(f.read()).hexdigest()

                if hash_ != sha256:
                    raise ValueError(f'Model archive hash mismatch. path: {filename} expected: {hash_} actual: {sha256}')

            with ZipFile(filename, 'r') as zip_file:
                zip_file.extractall(self.model_path)

