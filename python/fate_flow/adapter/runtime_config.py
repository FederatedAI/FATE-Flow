import os
import importlib
from fate_flow.utils.file_utils import load_yaml_conf
from fate_flow.runtime.system_settings import THIRD_PARTY
from ofx.api.client import CommonSchedulerApi


class CommonRuntimeConfig(object):
    SERVICE_CONF: dict = {}
    SCHEDULE_CLIENT: CommonSchedulerApi = None
    DAG_SCHEMA = None

    @classmethod
    def load_schema_conf(cls):
        package = f"fate_flow.adapt.{THIRD_PARTY}.spec.job"
        DagSchemaSpec = getattr(importlib.import_module(package), "DagSchemaSpec")
        cls.DAG_SCHEMA = DagSchemaSpec

    @classmethod
    def load_service_conf(cls):
        name = "service_conf.yaml"
        service_conf_path = os.path.join(os.path.dirname(__file__), THIRD_PARTY, "conf", name)
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
            CommonSchedulerApi(
                remote_host=cls.SERVICE_CONF.get("conf").get("host"),
                remote_port=cls.SERVICE_CONF.get("conf").get("port"),
                client_cert=cls.SERVICE_CONF.get("conf").get("client_cert", None),
                client_key=cls.SERVICE_CONF.get("conf").get("client_key", None),
                client_ca=cls.SERVICE_CONF.get("conf").get("client_ca", None),
                token=cls.SERVICE_CONF.get("conf").get("client_cert", None),
                api_version=cls.SERVICE_CONF.get("version", None)
            )
        )

