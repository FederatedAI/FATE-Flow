#
#  Copyright 2022 The FATE Authors. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest import result

from fate_flow.db.runtime_config import RuntimeConfig
from fate_flow.entity import RetCode
from fate_flow.scheduler import SchedulerBase
from fate_flow.utils.api_utils import cluster_api
from fate_flow.utils.log_utils import failed_log, schedule_logger, start_log


class ClusterScheduler(SchedulerBase):

    @classmethod
    def cluster_command(cls, endpoint, json_body):
        log_msg = f'sending {endpoint} cluster federated command'
        schedule_logger().info(start_log(msg=log_msg))

        instance_list = RuntimeConfig.SERVICE_DB.get_servers()
        result = {}

        with ThreadPoolExecutor(max_workers=len(instance_list)) as executor:
            futures = {
                executor.submit(
                    cluster_api,
                    method='POST',
                    host=instance.host,
                    port=instance.http_port,
                    endpoint=endpoint,
                    json_body=json_body,
                ): instance_id
                for instance_id, instance in instance_list.items()
            }

            for future in as_completed(futures):
                instance = instance_list[futures[future]]

                try:
                    response = future.result()
                except Exception as e:
                    schedule_logger().exception(e)

                    response = {
                        'retcode': RetCode.FEDERATED_ERROR,
                        'retmsg': f'Federated schedule error: {instance.instance_id}\n{e}',
                    }
                else:
                    if response['retcode'] != RetCode.SUCCESS:
                        schedule_logger().error(failed_log(msg=log_msg, detail=response))

                result[instance.instance_id] = response

        return result
