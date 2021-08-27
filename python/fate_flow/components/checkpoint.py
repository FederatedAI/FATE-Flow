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
from fate_flow.components._base import BaseParam, ComponentBase, ComponentMeta, ComponentInputProtocol
from fate_flow.model.checkpoint import CheckpointManager


checkpoint_cpn_meta = ComponentMeta('Checkpoint')


@checkpoint_cpn_meta.bind_runner.on_local
class CheckpointComponent(ComponentBase):

    def _run(self, cpn_input: ComponentInputProtocol):
        params = {}
        for i in ('model_id', 'model_version', 'component_name'):
            params[i] = cpn_input.parameters.get(i)
            if params[i] is None:
                raise TypeError(f'Component Checkpoint needs {i}')
        for i in ('step_index', 'step_name'):
            params[i] = cpn_input.parameters.get(i)

        checkpoint_manager = CheckpointManager(
            role=self.tracker.role, party_id=self.tracker.party_id,
            model_id=params['model_id'], model_version=params['model_version'],
            component_name=params['component_name'],
            mkdir=False,
        )

        if params['step_index'] is not None:
            checkpoint = checkpoint_manager.get_checkpoint_by_index(params['step_index'])
        elif params['step_name'] is not None:
            checkpoint = checkpoint_manager.get_checkpoint_by_name(params['step_name'])
        else:
            raise TypeError('Component Checkpoint needs step_index or step_name.')

        if checkpoint is None:
            raise TypeError('Checkpoint not found.')

        self.model_output = checkpoint.read()


@checkpoint_cpn_meta.bind_param
class CheckpointParam(BaseParam):

    def __init__(self, model_id: str = None, model_version: str = None, component_name: str = None,
                 step_index: int = None, step_name: str = None):
        self.model_id = model_id
        self.model_version = model_version
        self.component_name = component_name
        self.step_index = step_index
        self.step_name = step_name

        if self.step_index is not None:
            self.step_index = int(self.step_index)

    def check(self):
        for i in ('model_id', 'model_version', 'component_name'):
            if getattr(self, i) is None:
                return False

        # do not set step_index and step_name at the same time
        if self.step_index is not None:
            return self.step_name is None
        return self.step_name is not None
