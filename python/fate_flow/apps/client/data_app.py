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

from fate_flow.engine import storage
from fate_flow.entity.code import ReturnCode
from fate_flow.manager.data_manager import DataManager
from fate_flow.utils.api_utils import get_json_result, validate_request_json, validate_request_params
from fate_flow.utils.data_upload import Upload, UploadParam

page_name = "data"


@manager.route('/upload', methods=['POST'])
@validate_request_json(file=fields.String(required=True), head=fields.Bool(required=True),
                       namespace=fields.String(required=True), name=fields.String(required=True),
                       partitions=fields.Integer(required=True), storage_engine=fields.String(required=False),
                       destroy=fields.Bool(required=False), meta=fields.Dict(required=True))
def upload_data(file, head, partitions, namespace, name, meta, destroy=False, storage_engine=""):
    data = Upload().run(parameters=UploadParam(file=file, head=head, partitions=partitions, namespace=namespace,
                                               name=name, storage_engine=storage_engine, meta=meta, destroy=destroy))
    return get_json_result(code=ReturnCode.Base.SUCCESS, message="success", data=data)


@manager.route('/download', methods=['GET'])
@validate_request_params(name=fields.String(required=True), namespace=fields.String(required=True))
def download(namespace, name):
    data_table_meta = storage.StorageTableMeta(name=name, namespace=namespace)
    return DataManager.send_table(
        output_tables_meta={"table": data_table_meta},
        tar_file_name=f'download_data_{namespace}_{name}.tar.gz',
        need_head=True
    )