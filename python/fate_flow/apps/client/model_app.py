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
from tempfile import TemporaryDirectory

from flask import request
from webargs import fields

from fate_flow.errors.job import NoFoundFile
from fate_flow.manager.model.model_manager import PipelinedModel
from fate_flow.utils.api_utils import API


@manager.route('/load', methods=['POST'])
def load():
    # todo:
    return API.Output.json()


@manager.route('/migrate', methods=['POST'])
def migrate():
    # todo:
    return API.Output.json()


@manager.route('/local/export', methods=['POST'])
@API.Input.json(model_id=fields.String(required=True))
@API.Input.json(model_version=fields.String(required=True))
@API.Input.json(party_id=fields.String(required=True))
@API.Input.json(role=fields.String(required=True))
@API.Input.json(dir_path=fields.String(required=True))
def export(model_id, model_version, party_id, role, dir_path):
    file_list = PipelinedModel.export_model(
        model_id=model_id,
        model_version=model_version,
        party_id=party_id,
        role=role,
        dir_path=dir_path
    )
    return API.Output.json(data=file_list)


@manager.route('/import', methods=['POST'])
@API.Input.params(model_id=fields.String(required=True))
@API.Input.params(model_version=fields.String(required=True))
def import_model(model_id, model_version):
    file = request.files.get('file')
    if not file:
        raise NoFoundFile()
    with TemporaryDirectory() as temp_dir:
        path = os.path.join(temp_dir, file.name)
        file.save(path)
        PipelinedModel.import_model(model_id, model_version, path, temp_dir)
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
