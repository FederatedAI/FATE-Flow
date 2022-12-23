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

    @abc.abstractmethod
    def update_runtime_artifacts(self, task_parameters):
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
