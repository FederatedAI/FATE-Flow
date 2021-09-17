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
import abc
import typing

from fate_flow.utils.log_utils import getLogger
from fate_flow.components.param_extract import ParamExtract
from fate_flow.scheduling_apps.client.tracker_client import TrackerClient


LOGGER = getLogger()


class ComponentInputProtocol(metaclass=abc.ABCMeta):

    @property
    @abc.abstractmethod
    def parameters(self) -> dict:
        ...

    @property
    @abc.abstractmethod
    def flow_feeded_parameters(self) -> dict:
        ...

    @property
    @abc.abstractmethod
    def roles(self):
        ...

    @property
    @abc.abstractmethod
    def job_parameters(self):
        ...

    @property
    @abc.abstractmethod
    def tracker(self):
        ...

    @property
    @abc.abstractmethod
    def task_version_id(self):
        ...

    @property
    @abc.abstractmethod
    def checkpoint_manager(self):
        ...

    @property
    @abc.abstractmethod
    def datasets(self):
        ...

    @property
    @abc.abstractmethod
    def models(self):
        ...


class ComponentOutput:
    def __init__(self, data, models, cache: typing.List[tuple], serialize: bool = True) -> None:
        self._data = data
        if not isinstance(self._data, list):
            self._data = [data]

        self._models = models
        if self._models is None:
            self._models = {}

        self._cache = cache
        if not isinstance(self._cache, list):
            self._cache = [cache]

        self.serialize = serialize

    @property
    def data(self):
        return self._data

    @property
    def model(self):
        if not self.serialize:
            return self._models

        serialized_models: typing.Dict[str, typing.Tuple[str, bytes]] = {}

        for model_name, buffer_object in self._models.items():
            serialized_string = buffer_object.SerializeToString()
            if not serialized_string:
                from fate_arch.protobuf.python import default_empty_fill_pb2

                buffer_object = default_empty_fill_pb2.DefaultEmptyFillMessage()
                buffer_object.flag = "set"
                serialized_string = buffer_object.SerializeToString()
            pb_name = type(buffer_object).__name__
            serialized_models[model_name] = (pb_name, serialized_string)

        return serialized_models

    @property
    def cache(self):
        return self._cache


class ComponentBase(metaclass=abc.ABCMeta):

    def __init__(self):
        self.task_version_id = ""
        self.tracker: TrackerClient = None
        self.checkpoint_manager = None
        self.model_output = None
        self.data_output = None
        self.cache_output = None
        self.serialize = True

    @abc.abstractmethod
    def _run(self, cpn_input: ComponentInputProtocol):
        """to be implemented"""
        ...

    def _retry(self, cpn_input: ComponentInputProtocol):
        ...
        # raise NotImplementedError(f"_retry for {type(self)} not implemented")

    def run(self, cpn_input: ComponentInputProtocol, retry: bool = True):
        self.task_version_id = cpn_input.task_version_id
        self.tracker = cpn_input.tracker
        self.checkpoint_manager = cpn_input.checkpoint_manager

        method = (self._retry if retry and
                  self.checkpoint_manager is not None and
                  self.checkpoint_manager.latest_checkpoint is not None
                  else self._run)
        method(cpn_input)

        return ComponentOutput(data=self.save_data(), models=self.export_model(), cache=self.save_cache(), serialize=self.serialize)

    def save_data(self):
        return self.data_output

    def export_model(self):
        return self.model_output

    def save_cache(self):
        return self.cache_output


class _RunnerDecorator:
    def __init__(self, meta) -> None:
        self._roles = set()
        self._meta = meta

    @property
    def on_guest(self):
        self._roles.add("guest")
        return self

    @property
    def on_host(self):
        self._roles.add("host")
        return self

    @property
    def on_arbiter(self):
        self._roles.add("arbiter")
        return self

    @property
    def on_local(self):
        self._roles.add("local")
        return self

    def __call__(self, cls):
        if issubclass(cls, ComponentBase):
            for role in self._roles:
                self._meta._role_to_runner_cls[role] = cls
        else:
            raise NotImplementedError(f"type of {cls} not supported")

        return cls


class ComponentMeta:
    __name_to_obj: typing.Dict[str, "ComponentMeta"] = {}

    def __init__(self, name) -> None:
        self.name = name
        self._role_to_runner_cls = {}
        self._param_cls = None

        self.__name_to_obj[name] = self

    @property
    def bind_runner(self):
        return _RunnerDecorator(self)

    @property
    def bind_param(self):
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
        param_obj = self._param_cls().set_name(f"{self.name}#{cpn_name}")
        return param_obj

    def get_supported_roles(self):
        roles = set(self._role_to_runner_cls.keys())
        if not roles:
            raise ModuleNotFoundError(f"roles for {self.name} is empty")
        return roles


class BaseParam(object):

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
