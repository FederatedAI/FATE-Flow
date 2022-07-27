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
from re import T
from zipfile import ZipFile

from ruamel import yaml

from fate_flow.db.db_models import DB, PipelineComponentMeta
from fate_flow.db.db_utils import bulk_insert_into_db
from fate_flow.model import Locker
from fate_flow.settings import TEMP_DIRECTORY
from fate_flow.utils.base_utils import get_fate_flow_directory
from fate_flow.utils.log_utils import getLogger


LOGGER = getLogger()


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

        self.model_path = Path(get_fate_flow_directory('model_local_cache'), self.party_model_id, self.model_version)
        self.define_meta_path = self.model_path / 'define' / 'define_meta.yaml'
        self.variables_data_path = self.model_path / 'variables' / 'data'
        self.run_parameters_path = self.model_path / 'run_parameters'
        self.checkpoint_path = self.model_path / 'checkpoint'

        super().__init__(self.model_path)

    def exists(self, component_name, model_alias):
        return self.variables_data_path.is_dir() and set((self.variables_data_path / component_name / model_alias).iterdir())

    def get_define_meta_from_file(self):
        with self.lock, open(self.define_meta_path, 'r', encoding="utf-8") as f:
            return yaml.load(f)

    @DB.connection_context()
    def get_define_meta_from_db(self):
        query = PipelineComponentMeta.select().where(
            PipelineComponentMeta.f_model_id == self.model_id,
            PipelineComponentMeta.f_model_version == self.model_version,
            PipelineComponentMeta.f_role == self.role,
            PipelineComponentMeta.f_party_id == self.party_id,
        )
        return list(query)

    def read_define_meta(self, db_only=False):
        query = self.get_define_meta_from_db()
        if not query and not db_only:
            return self.get_define_meta_from_file()

        define_meta = {
            'component_define': {},
            'model_proto': {},
        }

        for row in query:
            define_meta['component_define'][row.f_component_name] = {'module_name': row.f_component_module_name}
            if row.f_component_name not in define_meta['model_proto']:
                define_meta['model_proto'][row.f_component_name] = {}
            define_meta['model_proto'][row.f_component_name][row.f_model_alias] = row.f_model_proto_index

        return define_meta

    @DB.connection_context()
    def write_define_meta(self, component_name, component_module_name, model_alias, model_proto_index):
        PipelineComponentMeta.insert(
            f_model_id=self.model_id,
            f_model_version=self.model_version,
            f_role=self.role,
            f_party_id=self.party_id,
            f_component_name=component_name,
            f_component_module_name=component_module_name,
            f_model_alias=model_alias,
            f_model_proto_index=model_proto_index,
        ).execute()

    def save_define_meta_from_db_to_file(self):
        define_meta = self.read_define_meta(True)

        with self.lock, open(self.define_meta_path, 'w', encoding='utf-8') as f:
            yaml.dump(define_meta, f, Dumper=yaml.RoundTripDumper)

    def save_define_meta_from_file_to_db(self):
        define_meta = self.get_define_meta_from_file()

        insert = []
        for component_name, component_define in define_meta['component_define'].items():
            for model_alias, model_proto_index in define_meta['model_proto'][component_name].items():
                row = {
                    'f_model_id': self.model_id,
                    'f_model_version': self.model_version,
                    'f_role': self.role,
                    'f_party_id': self.party_id,
                    'f_component_name': component_name,
                    'f_component_module_name': component_define['module_name'],
                    'f_model_alias': model_alias,
                    'f_model_proto_index': model_proto_index,
                }
                insert.append(row)

        with DB.connection_context():
            PipelineComponentMeta.delete().where(
                PipelineComponentMeta.f_model_id == self.model_id,
                PipelineComponentMeta.f_model_version == self.model_version,
                PipelineComponentMeta.f_role == self.role,
                PipelineComponentMeta.f_party_id == self.party_id,
            )
        bulk_insert_into_db(PipelineComponentMeta, insert, LOGGER)

    def replicate_define_meta(self, modification):
        query = self.get_define_meta_from_db()

        insert = []
        for row in query:
            row = row.to_dict()
            del row['id']

            for key, val in modification.items():
                row[key] = val

            insert.append(row)

        bulk_insert_into_db(PipelineComponentMeta, insert, LOGGER)

    def get_archive_path(self, component_name):
        return Path(TEMP_DIRECTORY, f'{self.party_model_id}_{self.model_version}_{component_name}.zip')

    def walk_component(self, zip_file, dir_path: Path):
        for path in dir_path.iterdir():
            if path.is_dir():
                self.walk_component(zip_file, path)
            else:
                zip_file.write(path, path.relative_to(self.model_path))

    def pack_component(self, component_name):
        filename = self.get_archive_path(component_name)

        with self.lock:
            with ZipFile(filename, 'w') as zip_file:
                self.walk_component(zip_file, self.variables_data_path / component_name)
                self.walk_component(zip_file, self.run_parameters_path / component_name)
                self.walk_component(zip_file, self.checkpoint_path / component_name)

            with open(filename, 'rb') as f:
                hash_ = hashlib.sha256(f.read()).hexdigest()

        return filename, hash_

    def unpack_component(self, component_name, hash_=None):
        filename = self.get_archive_path(component_name)

        with self.lock:
            if hash_ is not None:
                with open(filename, 'rb') as f:
                    sha256 = hashlib.sha256(f.read()).hexdigest()

                if hash_ != sha256:
                    raise ValueError(f'Model archive hash mismatch. path: {filename} expected: {hash_} actual: {sha256}')

            with ZipFile(filename, 'r') as zip_file:
                zip_file.extractall(self.model_path)

