import os
from importlib import import_module
from pathlib import Path


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


def load_adapter_db():
    """
    import the package to create a table.
    """
    for name in adapter_list:
        path = Path(__file__).parent / name / "db"
        adapter_module = get_module(path)
        try:
            import_module(".".join([adapter_module, "db"]))
        except Exception as e:
            # 'db' is not an essential package.
            pass


def load_adapter_apps(register_page, search_pages_path):
    urls_dict = {}
    for name in adapter_list:
        path = Path(__file__).parent / name / "apps"
        version = getattr(import_module(get_app_module(path)), "__version__", None)
        before_request_func = getattr(import_module(get_app_module(path)), "before_request", None)
        urls_dict[name] = [register_page(path, func=before_request_func, prefix=version) for path in search_pages_path(path)]
    return urls_dict


def init_adapter():
    load_adapter_db()
