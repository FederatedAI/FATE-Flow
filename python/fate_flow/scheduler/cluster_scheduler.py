from fate_flow.db.runtime_config import RuntimeConfig
from fate_flow.entity import RetCode
from fate_flow.scheduler import SchedulerBase
from fate_flow.settings import API_VERSION
from fate_flow.utils.api_utils import cluster_api
from fate_flow.utils.log_utils import schedule_logger, start_log, failed_log


class ClusterScheduler(SchedulerBase):
    @classmethod
    def update_provider(cls, info):
        federated_response = {}
        instance_list = RuntimeConfig.SERVICE_DB.get_servers()
        for instance in instance_list:
            cls.cluster_command(http_address=instance.http_address, endpoint="/provider/update", body=info,
                                federated_response=federated_response)
        return federated_response

    @classmethod
    def cluster_command(cls, http_address, endpoint, body, federated_response, api_version=API_VERSION):
        endpoint = f"/{api_version}{endpoint}"
        log_msg = f"sending {endpoint} cluster federated command"
        schedule_logger().info(start_log(msg=log_msg))
        try:
            response = cluster_api(method='POST',
                                   endpoint=endpoint,
                                   http_address=http_address,
                                   json_body=body if body else {}
                                   )
        except Exception as e:
            schedule_logger().exception(e)
            response = {
                "retcode": RetCode.FEDERATED_ERROR,
                "retmsg": "Federated schedule error, {}".format(e)
            }
        if response["retcode"] != RetCode.SUCCESS:
            schedule_logger().error(failed_log(msg=log_msg, detail=response))
        federated_response[http_address] = response
