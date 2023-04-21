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
    TASK_EXECUTOR = "task_executor"
    TASK_INITIALIZER = "task_initializer"
    PROVIDER_REGISTRAR = "provider_registrar"
    DEPENDENCE_UPLOAD = "dependence_upload"