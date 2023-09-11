import os
from importlib import import_module
from pathlib import Path


def load_adapter_name():
    return [
        name for name in os.listdir(Path(__file__).parent)
        if os.path.isdir(os.path.join(Path(__file__).parent, name)) and not name.endswith("__")
    ]


def load_adapter_apps(register_page, get_app_module, search_pages_path):
    adapter_list = load_adapter_name()
    urls_dict = {}
    for name in adapter_list:
        path = Path(__file__).parent / name / "apps"
        version = getattr(import_module(get_app_module(path)), "__version__", None)
        urls_dict[name] = [register_page(path, prefix=version) for path in search_pages_path(path)]
    return urls_dict
