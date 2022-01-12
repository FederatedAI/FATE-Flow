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
import io
import os
import tarfile

from flask import send_file, request

from fate_arch.common import file_utils
from fate_flow.settings import TEMPLATE_INFO_PATH
from fate_flow.utils.base_utils import get_fate_flow_directory


@manager.route('/download', methods=['post'])
def template_download():
    min_data = request.json.get("min_data", False) if request.json else False
    memory_file = io.BytesIO()
    dir_dict = {}
    template_info = file_utils.load_yaml_conf(TEMPLATE_INFO_PATH)
    data_dir = template_info.get("template_data", {}).get("base_dir")
    min_data_file = template_info.get("template_data", {}).get("min_data", [])
    for name, dir_name in template_info.get("template_path", {}).items():
        dir_dict[name] = os.path.join(get_fate_flow_directory(), dir_name)
    delete_dir_list = []
    for name, dir_list in template_info.get("delete_path").items():
        for dir_name in dir_list:
            delete_dir_list.append(os.path.join(dir_dict[name], dir_name))
    tar = tarfile.open(fileobj=memory_file, mode='w:gz')
    for name, base_dir in dir_dict.items():
        for root, dir, files in os.walk(base_dir):
            for file in files:
                if min_data:
                    if data_dir in root and file not in min_data_file:
                        continue
                if root in delete_dir_list:
                    continue
                full_path = os.path.join(root, file)
                rel_path = os.path.join(name, os.path.relpath(full_path, base_dir))
                tar.add(full_path, rel_path)
    tar.close()
    memory_file.seek(0)
    return send_file(memory_file, attachment_filename=f'template.tar.gz', as_attachment=True)