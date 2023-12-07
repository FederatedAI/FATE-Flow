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
from fate_flow.runtime.system_settings import FATE_FLOW_JOB_DEFAULT_CONFIG_PATH
from .reload_config_base import ReloadConfigBase
from ..utils import file_utils
from ..utils.log import getLogger

stat_logger = getLogger()


class JobDefaultConfig(ReloadConfigBase):
    job_cores = None
    computing_partitions = None
    task_run = None
    remote_request_timeout = None
    federated_command_trys = None
    job_timeout = None
    auto_retries = None
    sync_type = None

    task_logger = None
    task_device = None
    task_timeout = None

    @classmethod
    def load(cls):
        conf = file_utils.load_yaml_conf(FATE_FLOW_JOB_DEFAULT_CONFIG_PATH)
        if not isinstance(conf, dict):
            raise ValueError("invalid config file")

        for k, v in conf.items():
            if hasattr(cls, k):
                setattr(cls, k, v)
            else:
                stat_logger.warning(f"job default config not supported {k}")

        return cls.get_all()
