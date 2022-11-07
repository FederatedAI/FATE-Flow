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
import shutil

from fate_arch.common.base_utils import json_dumps, json_loads

from fate_flow.db.db_models import PipelineComponentMeta
from fate_flow.model.checkpoint import CheckpointManager
from fate_flow.model.sync_model import SyncComponent, SyncModel
from fate_flow.operation.job_saver import JobSaver
from fate_flow.pipelined_model.pipelined_model import PipelinedModel
from fate_flow.settings import ENABLE_MODEL_STORE, stat_logger
from fate_flow.utils.base_utils import compare_version
from fate_flow.utils.config_adapter import JobRuntimeConfigAdapter
from fate_flow.utils.model_utils import (
    check_before_deploy, gather_model_info_data,
    gen_party_model_id, save_model_info,
)
from fate_flow.utils.schedule_utils import get_dsl_parser_by_version


def deploy(config_data):
    model_id = config_data['model_id']
    model_version = config_data['model_version']
    local_role = config_data['local']['role']
    local_party_id = config_data['local']['party_id']
    child_model_version = config_data['child_model_version']
    components_checkpoint = config_data.get('components_checkpoint', {})
    warning_msg = ""

    try:
        if ENABLE_MODEL_STORE:
            sync_model = SyncModel(
                role=local_role, party_id=local_party_id,
                model_id=model_id, model_version=model_version,
            )
            if sync_model.remote_exists():
                sync_model.download(True)

        party_model_id = gen_party_model_id(
            model_id=model_id,
            role=local_role,
            party_id=local_party_id,
        )
        source_model = PipelinedModel(party_model_id, model_version)
        deploy_model = PipelinedModel(party_model_id, child_model_version)

        if not source_model.exists():
            raise FileNotFoundError(f'Can not found {model_id} {model_version} model local cache.')

        if not check_before_deploy(source_model):
            raise Exception('Child model could not be deployed.')

        pipeline_model = source_model.read_pipeline_model()
        pipeline_model.model_version = child_model_version

        train_runtime_conf = json_loads(pipeline_model.train_runtime_conf)
        dsl_version = int(train_runtime_conf.get('dsl_version', 1))
        parser = get_dsl_parser_by_version(dsl_version)

        inference_dsl = config_data.get('predict_dsl', config_data.get('dsl'))

        if inference_dsl is not None:
            if dsl_version == 1:
                raise KeyError("'predict_dsl' is not supported in DSL v1")

            if 'cpn_list' in config_data:
                raise KeyError("'cpn_list' should not be set when 'predict_dsl' is set")

            if not isinstance(inference_dsl, dict):
                inference_dsl = json_loads(inference_dsl)
        else:
            if dsl_version == 1:
                if 'cpn_list' in config_data:
                    raise KeyError("'cpn_list' is not supported in DSL v1")

                inference_dsl, warning_msg = parser.convert_dsl_v1_to_v2(
                    json_loads(pipeline_model.inference_dsl),
                )
            else:
                train_dsl = json_loads(pipeline_model.train_dsl)
                inference_dsl = parser.deploy_component(
                    config_data.get(
                        'cpn_list',
                        list(train_dsl.get('components', {}).keys()),
                    ),
                    train_dsl,
                )

        cpn_list = list(inference_dsl.get('components', {}).keys())

        if dsl_version == 1:
            from fate_flow.db.component_registry import ComponentRegistry

            job_providers = parser.get_job_providers(
                dsl=inference_dsl,
                provider_detail=ComponentRegistry.REGISTRY,
            )
            train_runtime_conf = parser.convert_conf_v1_to_v2(
                train_runtime_conf,
                {
                    cpn: parser.parse_component_role_parameters(
                        component=cpn,
                        dsl=inference_dsl,
                        runtime_conf=train_runtime_conf,
                        provider_detail=ComponentRegistry.REGISTRY,
                        provider_name=job_providers[cpn]['provider']['name'],
                        provider_version=job_providers[cpn]['provider']['version'],
                    ) for cpn in cpn_list
                }
            )

        parser = get_dsl_parser_by_version()
        parser.verify_dsl(inference_dsl, 'predict')
        inference_dsl = JobSaver.fill_job_inference_dsl(
            job_id=model_version, role=local_role, party_id=local_party_id,
            dsl_parser=parser, origin_inference_dsl=inference_dsl,
        )
        pipeline_model.inference_dsl = json_dumps(inference_dsl, byte=True)

        train_runtime_conf = JobRuntimeConfigAdapter(
            train_runtime_conf,
        ).update_model_id_version(
            model_version=child_model_version,
        )
        pipeline_model.train_runtime_conf = json_dumps(train_runtime_conf, byte=True)

        if compare_version(pipeline_model.fate_version, '1.5.0') == 'gt':
            runtime_conf_on_party = json_loads(pipeline_model.runtime_conf_on_party)
            runtime_conf_on_party['job_parameters']['model_version'] = child_model_version
            pipeline_model.runtime_conf_on_party = json_dumps(runtime_conf_on_party, byte=True)

            pipeline_model.parent = False
            pipeline_model.parent_info = json_dumps({
                'parent_model_id': model_id,
                'parent_model_version': model_version,
            }, byte=True)

        query_args = (
            PipelineComponentMeta.f_component_name.in_(cpn_list),
        )
        query = source_model.pipelined_component.get_define_meta_from_db(*query_args)

        for row in query:
            shutil.copytree(
                source_model.pipelined_component.variables_data_path / row.f_component_name,
                deploy_model.pipelined_component.variables_data_path / row.f_component_name,
            )

        source_model.pipelined_component.replicate_define_meta({
            'f_model_version': child_model_version,
            'f_archive_sha256': None,
            'f_archive_from_ip': None,
        }, query_args)

        if ENABLE_MODEL_STORE:
            for row in query:
                sync_component = SyncComponent(
                    role=local_role, party_id=local_party_id,
                    model_id=model_id, model_version=child_model_version,
                    component_name=row.f_component_name,
                )
                sync_component.copy(model_version, row.f_archive_sha256)

        deploy_model.save_pipeline_model(pipeline_model)

        for row in query:
            step_index = components_checkpoint.get(row.f_component_name, {}).get('step_index')
            step_name = components_checkpoint.get(row.f_component_name, {}).get('step_name')
            if step_index is not None:
                step_index = int(step_index)
                step_name = None
            elif step_name is None:
                continue

            checkpoint_manager = CheckpointManager(
                role=local_role, party_id=local_party_id,
                model_id=model_id, model_version=model_version,
                component_name=row.f_component_name,
            )
            checkpoint_manager.load_checkpoints_from_disk()
            if checkpoint_manager.latest_checkpoint is not None:
                checkpoint_manager.deploy(
                    child_model_version,
                    row.f_model_alias,
                    step_index,
                    step_name,
                )

        deploy_model_info = gather_model_info_data(deploy_model)
        save_model_info(deploy_model_info)
    except Exception as e:
        stat_logger.exception(e)

        return 100, (
            f'deploy model of role {local_role} {local_party_id} failed, '
            f'details: {repr(e)}'
        )
    else:
        return 0, (
            f'deploy model of role {local_role} {local_party_id} success'
            + ('' if not warning_msg else f', warning: {warning_msg}')
        )
