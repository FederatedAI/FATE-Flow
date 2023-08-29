import sys
import fate_flow


def is_in_virtualenv():
    try:
        module_path = fate_flow.__file__
        return sys.prefix in module_path
    except ImportError:
        return False
