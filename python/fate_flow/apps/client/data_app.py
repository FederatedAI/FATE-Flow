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
from fate_flow.manager.data.data_manager import DataManager
from fate_flow.utils.api_utils import API
from fate_flow.utils.data_upload import Upload, UploadParam

page_name = "data"


@manager.route('/upload', methods=['POST'])
@API.Input.json(file=fields.String(required=True))
@API.Input.json(head=fields.Bool(required=True))
@API.Input.json(namespace=fields.String(required=True))
@API.Input.json(name=fields.String(required=True))
@API.Input.json(partitions=fields.Integer(required=True))
@API.Input.json(storage_engine=fields.String(required=False))
@API.Input.json(destroy=fields.Bool(required=False))
@API.Input.json(meta=fields.Dict(required=True))
def upload_data(file, head, partitions, namespace, name, meta, destroy=False, storage_engine=""):
    data = Upload().run(parameters=UploadParam(file=file, head=head, partitions=partitions, namespace=namespace,
                                               name=name, storage_engine=storage_engine, meta=meta, destroy=destroy))
    return API.Output.json(data=data)


@manager.route('/download', methods=['GET'])
@API.Input.params(name=fields.String(required=True))
@API.Input.params(namespace=fields.String(required=True))
def download(namespace, name):
    data_table_meta = storage.StorageTableMeta(name=name, namespace=namespace)
    return DataManager.send_table(
        output_tables_meta={"table": data_table_meta},
        tar_file_name=f'download_data_{namespace}_{name}.tar.gz',
        need_head=True
    )