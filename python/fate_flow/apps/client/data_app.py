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
from webargs import fields
from flask import request
from fate_flow.apps.desc import SERVER_FILE_PATH, HEAD, PARTITIONS, META, EXTEND_SID, NAMESPACE, NAME, DATA_WAREHOUSE, \
    DROP, SITE_NAME
from fate_flow.engine import storage
from fate_flow.manager.components.component_manager import ComponentManager
from fate_flow.manager.outputs.data import DataManager
from fate_flow.utils.api_utils import API
from fate_flow.errors.server_error import NoFoundTable, NoFoundFile

page_name = "data"


@manager.route('/component/upload', methods=['POST'])
@API.Input.json(file=fields.String(required=True), desc=SERVER_FILE_PATH)
@API.Input.json(head=fields.Bool(required=True), desc=HEAD)
@API.Input.json(partitions=fields.Integer(required=True), desc=PARTITIONS)
@API.Input.json(meta=fields.Dict(required=True), desc=META)
@API.Input.json(extend_sid=fields.Bool(required=False), desc=EXTEND_SID)
@API.Input.json(namespace=fields.String(required=False), desc=NAMESPACE)
@API.Input.json(name=fields.String(required=False), desc=NAME)
def upload_data(file, head, partitions, meta, namespace=None, name=None, extend_sid=False):
    result = ComponentManager.upload(
        file=file, head=head, partitions=partitions, meta=meta, namespace=namespace, name=name, extend_sid=extend_sid
    )
    return API.Output.json(**result)


@manager.route('/component/upload/file', methods=['POST'])
@API.Input.form(head=fields.Bool(required=True), desc=HEAD)
@API.Input.form(partitions=fields.Integer(required=True), desc=PARTITIONS)
@API.Input.form(meta=fields.String(required=True), desc=META)
@API.Input.form(extend_sid=fields.Bool(required=False), desc=EXTEND_SID)
@API.Input.form(namespace=fields.String(required=False), desc=NAMESPACE)
@API.Input.form(name=fields.String(required=False), desc=NAME)
def upload_file(head, partitions, meta, namespace=None, name=None, extend_sid=False):

    file = request.files.get('file')
    if not file:
        raise NoFoundFile()
    result = ComponentManager.upload_file(file=file, head=head, partitions=partitions, meta=json.loads(meta), namespace=namespace, name=name,
                                 extend_sid=extend_sid)

    return API.Output.json(**result)


@manager.route('/component/download', methods=['POST'])
@API.Input.json(name=fields.String(required=True), desc=NAME)
@API.Input.json(namespace=fields.String(required=True), desc=NAMESPACE)
@API.Input.json(path=fields.String(required=False), desc=SERVER_FILE_PATH)
def download_data(namespace, name, path):
    result = ComponentManager.download(
        path=path, namespace=namespace, name=name
    )
    return API.Output.json(**result)


@manager.route('/component/dataframe/transformer', methods=['POST'])
@API.Input.json(data_warehouse=fields.Dict(required=True), desc=DATA_WAREHOUSE)
@API.Input.json(namespace=fields.String(required=True), desc=NAMESPACE)
@API.Input.json(name=fields.String(required=True), desc=NAME)
@API.Input.json(site_name=fields.String(required=False), desc=SITE_NAME)
@API.Input.json(drop=fields.Bool(required=False), desc=DROP)
def transformer_data(data_warehouse, namespace, name, drop=True, site_name=None):
    result = ComponentManager.dataframe_transformer(data_warehouse, namespace, name, drop, site_name)
    return API.Output.json(**result)


@manager.route('/download', methods=['GET'])
@API.Input.params(name=fields.String(required=True), desc=NAME)
@API.Input.params(namespace=fields.String(required=True), desc=NAMESPACE)
@API.Input.params(header=fields.String(required=False), desc=HEAD)
def download(namespace, name, header=None):
    data_table_meta = storage.StorageTableMeta(name=name, namespace=namespace)
    if not data_table_meta:
        raise NoFoundTable(name=name, namespace=namespace)
    return DataManager.send_table(
        output_tables_meta={"data": data_table_meta},
        tar_file_name=f'download_data_{namespace}_{name}.tar.gz',
        need_head=header
    )

