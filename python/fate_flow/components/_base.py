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
import typing
from fate_arch.common import log
from fate_flow.components.param_extract import ParamExtract
from fate_flow.scheduling_apps.client.tracker_client import TrackerClient

LOGGER = log.getLogger()


class ComponentBase(object):
    def __init__(self):
        self.task_version_id = ""
        self.tracker: TrackerClient = None
        self.checkpoint_manager = None
        self.model_output = None
        self.data_output = None

    def run(self, component_parameters: dict = None, run_args: dict = None):
        pass

    def set_tracker(self, tracker: TrackerClient):
        self.tracker = tracker

    def set_checkpoint_manager(self, checkpoint_manager):
        self.checkpoint_manager = checkpoint_manager

    def save_data(self):
        return self.data_output

    def export_model(self):
        return self.model_output

    def set_task_version_id(self, task_version_id):
        self.task_version_id = task_version_id


class ComponentMeta:
    __name_to_obj: typing.Dict[str, "ComponentMeta"] = {}

    def __init__(self, name) -> None:
        self.name = name
        self._role_to_runner_cls = {}
        self._param_cls = None

        self.__name_to_obj[name] = self

    def impl_runner(self, *args: str):
        def _wrap(cls):
            for role in args:
                self._role_to_runner_cls[role] = cls
            return cls

        return _wrap

    @property
    def impl_param(self):
        def _wrap(cls):
            self._param_cls = cls
            return cls

        return _wrap

    def register_info(self):
        return {
            self.name: dict(
                module=self.__module__,
            )
        }

    @classmethod
    def get_meta(cls, name):
        return cls.__name_to_obj[name]

    def _get_runner(self, role: str):
        if role not in self._role_to_runner_cls:
            raise ModuleNotFoundError(
                f"Runner for component `{self.name}` at role `{role}` not found"
            )
        return self._role_to_runner_cls[role]

    def get_run_obj(self, role: str):
        return self._get_runner(role)()

    def get_run_obj_name(self, role: str) -> str:
        return self._get_runner(role).__name__

    def get_param_obj(self, cpn_name: str):
        if self._param_cls is None:
            raise ModuleNotFoundError(f"Param for component `{self.name}` not found")
        return self._param_cls().set_name(f"{self.name}#{cpn_name}")

    def get_supported_roles(self):
        return set(self._role_to_runner_cls.keys())


class BaseParam(object):
    def __init__(self):
        pass

    def set_name(self, name: str):
        self._name = name
        return self

    def check(self):
        raise NotImplementedError("Parameter Object should have be check")

    def as_dict(self):
        return ParamExtract().change_param_to_dict(self)

    @classmethod
    def from_dict(cls, conf):
        obj = cls()
        obj.update(conf)
        return obj

    def update(self, conf, allow_redundant=False):
        return ParamExtract().recursive_parse_param_from_config(
            param=self,
            config_json=conf,
            param_parse_depth=0,
            valid_check=not allow_redundant,
            name=self._name,
        )
