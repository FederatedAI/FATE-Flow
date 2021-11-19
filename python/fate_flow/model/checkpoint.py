#
#  Copyright 2021 The FATE Authors. All Rights Reserved.
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
import hashlib
from pathlib import Path
from typing import Dict, Tuple
from shutil import copytree, rmtree
from base64 import b64encode
from datetime import datetime
from collections import deque, OrderedDict

from ruamel import yaml

from fate_arch.common.base_utils import json_dumps, json_loads

from fate_flow.settings import stat_logger
from fate_flow.entity import RunParameters
from fate_flow.utils.model_utils import gen_party_model_id
from fate_flow.utils.base_utils import get_fate_flow_directory
from fate_flow.model import Locker


class Checkpoint(Locker):

    def __init__(self, directory: Path, step_index: int, step_name: str, mkdir: bool = True):
        self.step_index = step_index
        self.step_name = step_name
        self.mkdir = mkdir
        self.create_time = None
        directory = directory / f'{step_index}#{step_name}'
        if self.mkdir:
            directory.mkdir(0o755, True, True)
        self.database = directory / 'database.yaml'

        super().__init__(directory)

    @property
    def available(self):
        return self.database.exists()

    def save(self, model_buffers: Dict[str, Tuple[str, bytes, dict]]):
        if not model_buffers:
            raise ValueError('model_buffers is empty.')

        self.create_time = datetime.utcnow()
        data = {
            'step_index': self.step_index,
            'step_name': self.step_name,
            'create_time': self.create_time.isoformat(),
            'models': {},
        }

        model_data = {}
        for model_name, (pb_name, serialized_string, json_format_dict) in model_buffers.items():
            model_data[model_name] = (serialized_string, json_format_dict)

            data['models'][model_name] = {
                'sha1': hashlib.sha1(serialized_string).hexdigest(),
                'buffer_name': pb_name,
            }

        with self.lock:
            for model_name, model in data['models'].items():
                serialized_string, json_format_dict = model_data[model_name]
                (self.directory / f'{model_name}.pb').write_bytes(serialized_string)
                (self.directory / f'{model_name}.json').write_text(json_dumps(json_format_dict), 'utf8')

            self.database.write_text(yaml.dump(data, Dumper=yaml.RoundTripDumper), 'utf8')

        stat_logger.info(f'Checkpoint saved. path: {self.directory}')
        return self.directory

    def read_database(self):
        with self.lock:
            data = yaml.safe_load(self.database.read_text('utf8'))
            if data['step_index'] != self.step_index or data['step_name'] != self.step_name:
                raise ValueError('Checkpoint may be incorrect: step_index or step_name dose not match. '
                                 f'filepath: {self.database} '
                                 f'expected step_index: {self.step_index} actual step_index: {data["step_index"]} '
                                 f'expected step_name: {self.step_name} actual step_index: {data["step_name"]}')

        self.create_time = datetime.fromisoformat(data['create_time'])
        return data

    def read(self, parse_models: bool = True, include_database: bool = False):
        data = self.read_database()

        with self.lock:
            for model_name, model in data['models'].items():
                model['filepath_pb'] = self.directory / f'{model_name}.pb'
                model['filepath_json'] = self.directory / f'{model_name}.json'
                if not model['filepath_pb'].exists() or not model['filepath_json'].exists():
                    raise FileNotFoundError(
                        'Checkpoint is incorrect: protobuf file or json file not found. '
                        f'protobuf filepath: {model["filepath_pb"]} json filepath: {model["filepath_json"]}'
                    )

            model_data = {
                model_name: (
                    model['filepath_pb'].read_bytes(),
                    json_loads(model['filepath_json'].read_text('utf8')),
                )
                for model_name, model in data['models'].items()
            }

        for model_name, model in data['models'].items():
            serialized_string, json_format_dict = model_data[model_name]

            sha1 = hashlib.sha1(serialized_string).hexdigest()
            if sha1 != model['sha1']:
                raise ValueError('Checkpoint may be incorrect: hash dose not match. '
                                 f'filepath: {model["filepath"]} expected: {model["sha1"]} actual: {sha1}')

        data['models'] = {
            model_name: (
                model['buffer_name'],
                *model_data[model_name],
            ) if parse_models
            else b64encode(model_data[model_name][0]).decode('ascii')
            for model_name, model in data['models'].items()
        }
        return data if include_database else data['models']

    def remove(self):
        self.create_time = None
        rmtree(self.directory)
        if self.mkdir:
            self.directory.mkdir(0o755)

    def to_dict(self, include_models: bool = False):
        if not include_models:
            return self.read_database()
        return self.read(False, True)


class CheckpointManager:

    def __init__(self, job_id: str = None, role: str = None, party_id: int = None,
                 model_id: str = None, model_version: str = None,
                 component_name: str = None, component_module_name: str = None,
                 task_id: str = None, task_version: int = None,
                 job_parameters: RunParameters = None,
                 max_to_keep: int = None, mkdir: bool = True,
                 ):
        self.job_id = job_id
        self.role = role
        self.party_id = party_id
        self.model_id = model_id
        self.model_version = model_version
        self.party_model_id = gen_party_model_id(self.model_id, self.role, self.party_id)
        self.component_name = component_name if component_name else 'pipeline'
        self.module_name = component_module_name if component_module_name else 'Pipeline'
        self.task_id = task_id
        self.task_version = task_version
        self.job_parameters = job_parameters
        self.mkdir = mkdir

        self.directory = (Path(get_fate_flow_directory()) / 'model_local_cache' /
                          self.party_model_id / model_version / 'checkpoint' / self.component_name)
        if self.mkdir:
            self.directory.mkdir(0o755, True, True)

        if isinstance(max_to_keep, int):
            if max_to_keep <= 0:
                raise ValueError('max_to_keep must be positive')
        elif max_to_keep is not None:
            raise TypeError('max_to_keep must be an integer')
        self.checkpoints = deque(maxlen=max_to_keep)

    def load_checkpoints_from_disk(self):
        checkpoints = []
        for directory in self.directory.glob('*'):
            if not directory.is_dir() or '#' not in directory.name:
                continue

            step_index, step_name = directory.name.split('#', 1)
            checkpoint = Checkpoint(self.directory, int(step_index), step_name)

            if not checkpoint.available:
                continue
            checkpoints.append(checkpoint)

        self.checkpoints = deque(sorted(checkpoints, key=lambda i: i.step_index), self.max_checkpoints_number)

    @property
    def checkpoints_number(self):
        return len(self.checkpoints)

    @property
    def max_checkpoints_number(self):
        return self.checkpoints.maxlen

    @property
    def number_indexed_checkpoints(self):
        return OrderedDict((i.step_index, i) for i in self.checkpoints)

    @property
    def name_indexed_checkpoints(self):
        return OrderedDict((i.step_name, i) for i in self.checkpoints)

    def get_checkpoint_by_index(self, step_index: int):
        return self.number_indexed_checkpoints.get(step_index)

    def get_checkpoint_by_name(self, step_name: str):
        return self.name_indexed_checkpoints.get(step_name)

    @property
    def latest_checkpoint(self):
        if self.checkpoints:
            return self.checkpoints[-1]

    @property
    def latest_step_index(self):
        if self.latest_checkpoint is not None:
            return self.latest_checkpoint.step_index

    @property
    def latest_step_name(self):
        if self.latest_checkpoint is not None:
            return self.latest_checkpoint.step_name

    def new_checkpoint(self, step_index: int, step_name: str):
        popped_checkpoint = None
        if self.max_checkpoints_number and self.checkpoints_number >= self.max_checkpoints_number:
            popped_checkpoint = self.checkpoints[0]

        checkpoint = Checkpoint(self.directory, step_index, step_name)
        self.checkpoints.append(checkpoint)

        if popped_checkpoint is not None:
            popped_checkpoint.remove()

        return checkpoint

    def clean(self):
        self.checkpoints = deque(maxlen=self.max_checkpoints_number)
        rmtree(self.directory)
        if self.mkdir:
            self.directory.mkdir(0o755)

    def deploy(self, new_model_version: str, model_alias: str, step_index: int = None, step_name: str = None):
        if step_index is not None:
            checkpoint = self.get_checkpoint_by_index(step_index)
        elif step_name is not None:
            checkpoint = self.get_checkpoint_by_name(step_name)
        else:
            raise KeyError('step_index or step_name is required.')

        if checkpoint is None:
            raise TypeError('Checkpoint not found.')
        # check files hash
        checkpoint.read()

        directory = Path(get_fate_flow_directory()) / 'model_local_cache' / self.party_model_id / new_model_version
        target = directory / 'variables' / 'data' / self.component_name / model_alias
        locker = Locker(directory)

        with locker.lock:
            rmtree(target, True)
            copytree(checkpoint.directory, target,
                     ignore=lambda src, names: {i for i in names if i.startswith('.')})

            for f in target.glob('*.pb'):
                f.replace(f.with_suffix(''))

    def to_dict(self, include_models: bool = False):
        return [checkpoint.to_dict(include_models) for checkpoint in self.checkpoints]
