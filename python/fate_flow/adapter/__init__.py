import inspect
import os
from importlib import import_module
from pathlib import Path

from fate_flow.scheduler import SchedulerABC
from fate_flow.utils.cron import Cron
from .runtime_config import CommonRuntimeConfig


def load_adapter_name():
    return [
        name for name in os.listdir(Path(__file__).parent)
        if os.path.isdir(os.path.join(Path(__file__).parent, name)) and not name.endswith("__")
    ]


adapter_list = load_adapter_name()


def get_app_module(page_path):
    page_name = page_path.stem.rstrip('app').rstrip("_")
    return ".".join([get_module(page_path), page_name])


def get_module(page_path):
    module_name = '.'.join(page_path.parts[page_path.parts.index('fate_flow') + 2:-1])
    return module_name


def load_adapter_module(module_name):
    packages = []
    for name in adapter_list:
        path = Path(__file__).parent / name / module_name
        adapter_module = get_module(path)
        try:
            packages.append(import_module(".".join([adapter_module, module_name])))
        except Exception as e:
            pass
    return packages


def load_scheduler():
    packages = load_adapter_module("scheduler")
    print(packages)
    for package in packages:
        members = inspect.getmembers(package)
        class_list = [member[1] for member in members if inspect.isclass(member[1])]
        print(class_list)
        for _class in class_list:
            if issubclass(_class, SchedulerABC):
                # start scheduler
                _class(interval=2 * 1000).start()

            elif issubclass(_class, Cron):
                print(_class)
                _class(interval=5 * 1000).start()


def load_db():
    load_adapter_module("db")


def load_adapter_apps(register_page, search_pages_path):
    urls_dict = {}
    for name in adapter_list:
        path = Path(__file__).parent / name / "apps"
        version = getattr(import_module(get_app_module(path)), "__version__", None)
        before_request_func = getattr(import_module(get_app_module(path)), "before_request", None)
        urls_dict[name] = [register_page(path, func=before_request_func, prefix=version) for path in
                           search_pages_path(path)]
    return urls_dict


def init_adapter():
    load_db()
    load_scheduler()
    CommonRuntimeConfig.init()
