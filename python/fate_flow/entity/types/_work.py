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
from fate_flow.entity import CustomEnum


class ProcessRole(CustomEnum):
    DRIVER = "driver"
    WORKER = "worker"


class WorkerName(CustomEnum):
    TASK_SUBMIT = "submit"
    TASK_ENTRYPOINT = "task_entrypoint"
    TASK_EXECUTE = "task_execute"
    COMPONENT_DEFINE = "component_define"
    TASK_CLEAN = "task_clean"
    TASK_EXECUTE_CLEAN = "execute_clean"
