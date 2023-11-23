from fate_flow.adapter.kuscia.utils.conf_utils import load_service_conf

remote_host = load_service_conf().get("conf").get("host"),
remote_port = load_service_conf().get("conf").get("port"),
client_cert = load_service_conf().get("conf").get("client_cert", None),
client_key = load_service_conf().get("conf").get("client_key", None),
client_ca = load_service_conf().get("conf").get("client_ca", None),
token = load_service_conf().get("conf").get("client_cert", None),
api_version = load_service_conf().get("version", None)

URLS = {
    "CreateJob": "/api/v1/job/create",
    "QueryJob": "/api/v1/job/query",
    "QueryBatchJob": "/api/v1/job/status/batchQuery",
    "DeleteJob": "/api/v1/job/delete",
    "StopJob": "/api/v1/job/stop"
}