#
#  Copyright 2021 The FATE Authors. All Rights Reserved.
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
from flask import request

from fate_arch.common.file_utils import get_federatedml_setting_conf_directory

from fate_flow.component_env_utils.env_utils import get_class_object
from fate_flow.db.component_registry import ComponentRegistry
from fate_flow.db.db_models import PipelineComponentMeta
from fate_flow.model.sync_model import SyncComponent
from fate_flow.pipelined_model.pipelined_model import PipelinedModel
from fate_flow.settings import ENABLE_MODEL_STORE
from fate_flow.utils.api_utils import error_response, get_json_result, validate_request
from fate_flow.utils.detect_utils import check_config
from fate_flow.utils.job_utils import generate_job_id
from fate_flow.utils.model_utils import gen_party_model_id
from fate_flow.utils.schedule_utils import get_dsl_parser_by_version


@manager.route('/get', methods=['POST'])
def get_components():
    return get_json_result(data=ComponentRegistry.get_components())


@manager.route('/<component_name>/get', methods=['POST'])
def get_component(component_name):
    return get_json_result(data=ComponentRegistry.get_components().get(component_name))


@manager.route('/validate', methods=['POST'])
def validate_component_param():
    if not request.json or not isinstance(request.json, dict):
        return error_response(400)

    required_keys = [
        'component_name',
        'component_module_name',
    ]
    config_keys = ['role']

    dsl_version = int(request.json.get('dsl_version', 0))
    parser_class = get_dsl_parser_by_version(dsl_version)
    if dsl_version == 1:
        config_keys += ['role_parameters', 'algorithm_parameters']
    elif dsl_version == 2:
        config_keys += ['component_parameters']
    else:
        return error_response(400, 'unsupported dsl_version')

    try:
        check_config(request.json, required_keys + config_keys)
    except Exception as e:
        return error_response(400, str(e))

    try:
        parser_class.validate_component_param(
            get_federatedml_setting_conf_directory(),
            {i: request.json[i] for i in config_keys},
            *[request.json[i] for i in required_keys])
    except Exception as e:
        return error_response(400, str(e))

    return get_json_result()


@manager.route('/hetero/merge', methods=['POST'])
@validate_request(
    'model_id', 'model_version', 'guest_party_id', 'host_party_ids',
    'component_name', 'model_type', 'output_format',
)
def hetero_model_merge():
    request_data = request.json

    if ENABLE_MODEL_STORE:
        sync_component = SyncComponent(
            role='guest',
            party_id=request_data['guest_party_id'],
            model_id=request_data['model_id'],
            model_version=request_data['model_version'],
            component_name=request_data['component_name'],
        )
        if not sync_component.local_exists() and sync_component.remote_exists():
            sync_component.download()

        for party_id in request_data['host_party_ids']:
            sync_component = SyncComponent(
                role='host',
                party_id=party_id,
                model_id=request_data['model_id'],
                model_version=request_data['model_version'],
                component_name=request_data['component_name'],
            )
            if not sync_component.local_exists() and sync_component.remote_exists():
                sync_component.download()

    model = PipelinedModel(
        gen_party_model_id(
            request_data['model_id'],
            'guest',
            request_data['guest_party_id'],
        ),
        request_data['model_version'],
    ).read_component_model(
        request_data['component_name'],
        output_json=True,
    )

    guest_param = None
    guest_meta = None

    for k, v in model.items():
        if k.endswith('Param'):
            guest_param = v
        elif k.endswith('Meta'):
            guest_meta = v
        else:
            return error_response(400, f'Unknown guest model key: "{k}".')

    if guest_param is None or guest_meta is None:
        return error_response(400, 'Invalid guest model.')

    host_params = []
    host_metas = []

    for party_id in request_data['host_party_ids']:
        model = PipelinedModel(
            gen_party_model_id(
                request_data['model_id'],
                'host',
                party_id,
            ),
            request_data['model_version'],
        ).read_component_model(
            request_data['component_name'],
            output_json=True,
        )

        for k, v in model.items():
            if k.endswith('Param'):
                host_params.append(v)
            elif k.endswith('Meta'):
                host_metas.append(v)
            else:
                return error_response(400, f'Unknown host model key: "{k}".')

    if not host_params or not host_metas or len(host_params) != len(host_metas):
        return error_response(400, 'Invalid host models.')

    data = get_class_object('hetero_model_merge')(
        guest_param, guest_meta,
        host_params, host_metas,
        request_data['model_type'],
        request_data['output_format'],
        request_data.get('target_name', 'y'),
        request_data.get('host_rename', False),
        request_data.get('include_guest_coef', False),
    )
    return get_json_result(data=data)


@manager.route('/woe_array/extract', methods=['POST'])
@validate_request(
    'model_id', 'model_version', 'role', 'party_id', 'component_name',
)
def woe_array_extract():
    if request.json['role'] != 'guest':
        return error_response(400, 'Only support guest role.')

    if ENABLE_MODEL_STORE:
        sync_component = SyncComponent(
            role=request.json['role'],
            party_id=request.json['party_id'],
            model_id=request.json['model_id'],
            model_version=request.json['model_version'],
            component_name=request.json['component_name'],
        )
        if not sync_component.local_exists() and sync_component.remote_exists():
            sync_component.download()

    model = PipelinedModel(
        gen_party_model_id(
            request.json['model_id'],
            request.json['role'],
            request.json['party_id'],
        ),
        request.json['model_version'],
    ).read_component_model(
        request.json['component_name'],
        output_json=True,
    )

    param = None
    meta = None

    for k, v in model.items():
        if k.endswith('Param'):
            param = v
        elif k.endswith('Meta'):
            meta = v
        else:
            return error_response(400, f'Unknown model key: "{k}".')

    if param is None or meta is None:
        return error_response(400, 'Invalid model.')

    data = get_class_object('extract_woe_array_dict')(param)
    return get_json_result(data=data)


@manager.route('/woe_array/merge', methods=['POST'])
@validate_request(
    'model_id', 'model_version', 'role', 'party_id', 'component_name', 'woe_array',
)
def woe_array_merge():
    if request.json['role'] != 'host':
        return error_response(400, 'Only support host role.')

    pipelined_model = PipelinedModel(
        gen_party_model_id(
            request.json['model_id'],
            request.json['role'],
            request.json['party_id'],
        ),
        request.json['model_version'],
    )

    query = pipelined_model.pipelined_component.get_define_meta_from_db(
        PipelineComponentMeta.f_component_name == request.json['component_name'],
    )
    if not query:
        return error_response(404, 'Component not found.')
    query = query[0]

    if ENABLE_MODEL_STORE:
        sync_component = SyncComponent(
            role=query.f_role,
            party_id=query.f_party_id,
            model_id=query.f_model_id,
            model_version=query.f_model_version,
            component_name=query.f_component_name,
        )
        if not sync_component.local_exists() and sync_component.remote_exists():
            sync_component.download()

    model = pipelined_model._read_component_model(
        query.f_component_name,
        query.f_model_alias,
    )

    for model_name, (
        buffer_name,
        buffer_string,
        buffer_dict,
    ) in model.items():
        if model_name.endswith('Param'):
            string_merged, dict_merged = get_class_object('merge_woe_array_dict')(
                buffer_name,
                buffer_string,
                buffer_dict,
                request.json['woe_array'],
            )
            model[model_name] = (
                buffer_name,
                string_merged,
                dict_merged,
            )
            break

    pipelined_model = PipelinedModel(
        pipelined_model.party_model_id,
        generate_job_id()
    )

    pipelined_model.save_component_model(
        query.f_component_name,
        query.f_component_module_name,
        query.f_model_alias,
        model,
        query.f_run_parameters,
    )

    if ENABLE_MODEL_STORE:
        sync_component = SyncComponent(
            role=query.f_role,
            party_id=query.f_party_id,
            model_id=query.f_model_id,
            model_version=pipelined_model.model_version,
            component_name=query.f_component_name,
        )
        sync_component.upload()

    return get_json_result(data={
        'role': query.f_role,
        'party_id': query.f_party_id,
        'model_id': query.f_model_id,
        'model_version': pipelined_model.model_version,
        'component_name': query.f_component_name,
    })
