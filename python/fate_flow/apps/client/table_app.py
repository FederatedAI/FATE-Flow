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

from fate_flow.apps.desc import NAMESPACE, NAME, DISPLAY, SERVER_FILE_PATH
from fate_flow.engine import storage
from fate_flow.engine.storage import Session, StorageEngine
from fate_flow.entity.code import ReturnCode
from fate_flow.errors.server_error import NoFoundTable
from fate_flow.manager.data.data_manager import DataManager
from fate_flow.utils.api_utils import API

page_name = "table"


@manager.route('/query', methods=['GET'])
@API.Input.params(namespace=fields.String(required=True), desc=NAMESPACE)
@API.Input.params(name=fields.String(required=True), desc=NAME)
@API.Input.params(display=fields.Bool(required=False), desc=DISPLAY)
def query_table(namespace, name, display=False):
    data, display_data = DataManager.get_data_info(namespace, name)
    if data:
        if display:
            data.update({"display": display_data})
        return API.Output.json(data=data)
    else:
        return API.Output.fate_flow_exception(NoFoundTable(name=name, namespace=namespace))


@manager.route('/delete', methods=['POST'])
@API.Input.json(namespace=fields.String(required=True), desc=NAMESPACE)
@API.Input.json(name=fields.String(required=True), desc=NAME)
def delete_table(namespace, name):
    if DataManager.delete_data(namespace, name):
        return API.Output.json()
    else:
        return API.Output.fate_flow_exception(NoFoundTable(name=name, namespace=namespace))


@manager.route('/bind/path', methods=['POST'])
@API.Input.json(namespace=fields.String(required=True), desc=NAMESPACE)
@API.Input.json(name=fields.String(required=True), desc=NAME)
@API.Input.json(path=fields.String(required=True), desc=SERVER_FILE_PATH)
def bind_path(namespace, name, path):
    address = storage.StorageTableMeta.create_address(storage_engine=StorageEngine.PATH, address_dict={"path": path})
    storage_meta = storage.StorageTableBase(
        namespace=namespace, name=name, address=address,
        engine=StorageEngine.PATH, options=None, partitions=None,
        key_serdes_type=0,
        value_serdes_type=0,
        partitioner_type=0,
    )
    storage_meta.create_meta()
    return API.Output.json()
