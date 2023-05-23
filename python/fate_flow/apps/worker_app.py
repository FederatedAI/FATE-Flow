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
import os.path

from flask import request

from fate_arch.common.file_utils import load_json_conf
from fate_flow.utils.api_utils import get_json_result

page_name = "worker"


@manager.route('/config/load', methods=['POST'])
def load_config():
    conf_path = request.json.get('config_path')
    data = {}
    if os.path.exists(conf_path):
        data = load_json_conf(conf_path)
    return get_json_result(data=data)
