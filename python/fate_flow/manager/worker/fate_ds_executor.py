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
import json
import os
import sys

from fate_flow.runtime.system_settings import DEEPSPEED_LOGS_DIR_PLACEHOLDER, DEEPSPEED_MODEL_DIR_PLACEHOLDER, \
    DEEPSPEED_RESULT_PLACEHOLDER


class FateSubmit:
    @staticmethod
    def run():
        import runpy
        runpy.run_module(mod_name='fate.components', run_name='__main__')


if __name__ == "__main__":
    # replace deepspeed rank env
    print(os.environ.get("EGGROLL_DEEPSPEED_CONTAINER_LOGS_DIR"))
    print(os.environ.get("EGGROLL_DEEPSPEED_CONTAINER_MODELS_DIR"))
    print(os.environ.get("EGGROLL_DEEPSPEED_CONTAINER_RESULT_DIR"))

    result_index = sys.argv.index("--execution-final-meta-path") + 1
    result_path = os.environ.get(sys.argv[result_index], "")

    env_name_index = sys.argv.index("--env-name") + 1
    env_key = sys.argv[env_name_index]
    sys.argv[result_index] = sys.argv[result_index].replace(
        DEEPSPEED_RESULT_PLACEHOLDER,
        os.environ.get("EGGROLL_DEEPSPEED_CONTAINER_RESULT_DIR")
    )

    env_str = os.environ.get(sys.argv[env_name_index], "")
    env_str = env_str.replace(DEEPSPEED_LOGS_DIR_PLACEHOLDER, os.environ.get("EGGROLL_DEEPSPEED_CONTAINER_LOGS_DIR"))
    env_str = env_str.replace(DEEPSPEED_MODEL_DIR_PLACEHOLDER, os.environ.get("EGGROLL_DEEPSPEED_CONTAINER_MODELS_DIR"))
    print(json.loads(env_str))
    os.environ[env_key] = env_str
    FateSubmit.run()
