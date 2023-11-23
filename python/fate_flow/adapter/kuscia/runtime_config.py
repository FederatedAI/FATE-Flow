import os
import importlib
from fate_flow.utils.file_utils import load_yaml_conf
from fate_flow.adapter.kuscia.utils.resource import KusciaApiClient
from .settings import remote_host, remote_port, client_key, client_ca, client_cert, token, api_version


class KusciaRuntimeConfig(object):
    SERVICE_CONF: dict = {}
    SCHEDULE_CLIENT: KusciaApiClient = None
    DAG_SCHEMA = None

    @classmethod
    def load_schema_conf(cls):
        package = f"fate_flow.adapt.kuscia.spec.job"
        DagSchemaSpec = getattr(importlib.import_module(package), "DagSchemaSpec")
        cls.DAG_SCHEMA = DagSchemaSpec

    @classmethod
    def load_service_conf(cls):
        name = "service_conf.yaml"
        service_conf_path = os.path.join(os.path.dirname(__file__), "conf", name)
        cls.SERVICE_CONF.update(load_yaml_conf(service_conf_path))

    @classmethod
    def set_schedule_client(cls, schedule_client):
        cls.SCHEDULE_CLIENT = schedule_client

    @classmethod
    def init(cls):
        # init service conf
        cls.load_service_conf()
        cls.load_schema_conf()

        cls.set_schedule_client(
            KusciaApiClient(
                remote_host=remote_host,
                remote_port=remote_port,
                client_cert=client_cert,
                client_key=client_key,
                client_ca=client_ca,
                token=token,
                api_version=api_version
            )
        )