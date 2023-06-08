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
from webargs import fields

from fate_flow.utils.api_utils import API


@manager.route('/load', methods=['POST'])
def load():
    # todo:
    return API.Output.json()


@manager.route('/migrate', methods=['POST'])
def migrate():
    # todo:
    return API.Output.json()


@manager.route('/export', methods=['POST'])
def export():
    # todo:
    return API.Output.json()


@manager.route('/import', methods=['POST'])
def import_model():
    # todo:
    return API.Output.json()


@manager.route('/delete', methods=['POST'])
def delete_model():
    # todo:
    return API.Output.json()


@manager.route('/store', methods=['POST'])
def store():
    # todo:
    return API.Output.json()


@manager.route('/restore', methods=['POST'])
def restore():
    # todo:
    return API.Output.json()
