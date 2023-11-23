
import os
import yaml
from ruamel import yaml


def load_yaml_conf(conf_path):
    try:
        with open(conf_path) as f:
            return yaml.safe_load(f)
    except Exception as e:
        raise EnvironmentError("loading yaml file config from {} failed:".format(conf_path), e)


def load_service_conf():
    name = "service_conf.yaml"
    service_conf_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "conf", name)
    return load_yaml_conf(service_conf_path)




