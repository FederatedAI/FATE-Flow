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
import abc
from abc import ABCMeta


class TaskParserABC(metaclass=ABCMeta):
    @property
    @abc.abstractmethod
    def need_run(self):
        ...

    @property
    @abc.abstractmethod
    def component_ref(self):
        ...

    @property
    @abc.abstractmethod
    def task_parameters(self):
        ...


class JobParserABC(metaclass=ABCMeta):
    @property
    @abc.abstractmethod
    def topological_sort(self):
        ...

    @classmethod
    @abc.abstractmethod
    def infer_dependent_tasks(cls, task_input):
        ...

    @abc.abstractmethod
    def get_task_node(self, task_name):
        ...

    @property
    def task_parser(self):
        return TaskParserABC

    @abc.abstractmethod
    def component_ref_list(self, role, party_id):
        ...

    @abc.abstractmethod
    def dataset_list(self, role, party_id):
        ...

    @abc.abstractmethod
    def role_parameters(self, role, party_id):
        ...
