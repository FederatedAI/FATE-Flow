#
#  Copyright 2019 The FATE Authors. All Rights Reserved.
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
from fate_flow.utils.log_utils import getLogger
from fate_flow.controller.task_controller import TaskController
from fate_flow.entity import ComponentProvider
from fate_flow.manager.provider_manager import ProviderManager
from fate_flow.utils import schedule_utils
from fate_flow.worker.base_worker import BaseWorker
from fate_flow.utils.log_utils import start_log, successful_log

LOGGER = getLogger()


class TaskInitializer(BaseWorker):
    def _run(self):
        result = {}
        dsl_parser = schedule_utils.get_job_dsl_parser(dsl=self.args.dsl,
                                                       runtime_conf=self.args.runtime_conf,
                                                       train_runtime_conf=self.args.train_runtime_conf,
                                                       pipeline_dsl=self.args.pipeline_dsl)

        provider = ComponentProvider(**self.args.config["provider"])
        common_task_info = self.args.config["common_task_info"]
        log_msg = f"initialize the components: {self.args.config['components']}"
        LOGGER.info(start_log(log_msg, role=self.args.role, party_id=self.args.party_id))
        for component_name in self.args.config["components"]:
            result[component_name] = {}
            task_info = {}
            task_info.update(common_task_info)

            parameters, user_specified_parameters = ProviderManager.get_component_parameters(dsl_parser=dsl_parser,
                                                                                             component_name=component_name,
                                                                                             role=self.args.role,
                                                                                             party_id=self.args.party_id,
                                                                                             provider=provider)
            if parameters:
                task_info = {}
                task_info.update(common_task_info)
                task_info["component_name"] = component_name
                task_info["component_module"] = parameters["module"]
                task_info["provider_info"] = provider.to_dict()
                task_info["component_parameters"] = parameters
                TaskController.create_task(role=self.args.role, party_id=self.args.party_id,
                                           run_on_this_party=common_task_info["run_on_this_party"],
                                           task_info=task_info)
                result[component_name]["need_run"] = True
            else:
                # The party does not need to run, pass
                result[component_name]["need_run"] = False
        LOGGER.info(successful_log(log_msg, role=self.args.role, party_id=self.args.party_id))
        return result


if __name__ == "__main__":
    TaskInitializer().run()
