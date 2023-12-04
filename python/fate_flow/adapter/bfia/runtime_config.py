import os.path

from fate_flow.runtime.system_settings import HOST, HTTP_PORT
from fate_flow.adapter.bfia.settings import LOCAL_SITE_ID as PARTY_ID
from fate_flow.settings import HTTP_REQUEST_TIMEOUT
from fate_flow.utils.file_utils import load_yaml_conf
from ofx.api.client import BfiaSchedulerApi


class BfiaRuntimeConfig(object):
    ROUTE_TABLE: dict = {}
    SCHEDULE_CLIENT: BfiaSchedulerApi = None

    @classmethod
    def load_route_table_from_file(cls):
        name = "route_table.yaml"
        route_table_path = os.path.join(os.path.dirname(__file__), "conf", name)
        cls.ROUTE_TABLE.update(load_yaml_conf(route_table_path))

    @classmethod
    def set_schedule_client(cls, schedule_client):
        cls.SCHEDULE_CLIENT = schedule_client

    @classmethod
    def init(cls):
        # init route table
        cls.load_route_table_from_file()

        # init schedule client
        cls.set_schedule_client(
            BfiaSchedulerApi(
                host=HOST,
                port=HTTP_PORT,
                timeout=HTTP_REQUEST_TIMEOUT,
                route_table=cls.ROUTE_TABLE,
                self_node_id=PARTY_ID
            )
        )
