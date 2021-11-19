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
import os
import shutil

from fate_arch.common.base_utils import json_loads, json_dumps

from fate_flow.settings import stat_logger
from fate_flow.pipelined_model.pipelined_model import PipelinedModel
from fate_flow.model.checkpoint import CheckpointManager
from fate_flow.utils.config_adapter import JobRuntimeConfigAdapter
from fate_flow.utils.model_utils import (gen_party_model_id, check_before_deploy, compare_version,
                                         gather_model_info_data, save_model_info)
from fate_flow.utils.schedule_utils import get_dsl_parser_by_version
from fate_flow.operation.job_saver import JobSaver


def deploy(config_data):
    model_id = config_data.get('model_id')
    model_version = config_data.get('model_version')
    local_role = config_data.get('local').get('role')
    local_party_id = config_data.get('local').get('party_id')
    child_model_version = config_data.get('child_model_version')
    components_checkpoint = config_data.get('components_checkpoint', {})
    warning_msg = ""

    try:
        party_model_id = gen_party_model_id(model_id=model_id, role=local_role, party_id=local_party_id)
        model = PipelinedModel(model_id=party_model_id, model_version=model_version)
        model_data = model.collect_models(in_bytes=True)
        if "pipeline.pipeline:Pipeline" not in model_data:
            raise Exception("Can not found pipeline file in model.")

        # check if the model could be executed the deploy process (parent/child)
        if not check_before_deploy(model):
            raise Exception('Child model could not be deployed.')

        # copy proto content from parent model and generate a child model
        deploy_model = PipelinedModel(model_id=party_model_id, model_version=child_model_version)
        shutil.copytree(src=model.model_path, dst=deploy_model.model_path,
                        ignore=lambda src, names: {'checkpoint'} if src == model.model_path else {})
        pipeline_model = deploy_model.read_pipeline_model()

        train_runtime_conf = json_loads(pipeline_model.train_runtime_conf)
        runtime_conf_on_party = json_loads(pipeline_model.runtime_conf_on_party)
        dsl_version = train_runtime_conf.get("dsl_version", "1")

        parser = get_dsl_parser_by_version(dsl_version)
        train_dsl = json_loads(pipeline_model.train_dsl)
        parent_predict_dsl = json_loads(pipeline_model.inference_dsl)

        if config_data.get('dsl') or config_data.get('predict_dsl'):
            inference_dsl = config_data.get('dsl') if config_data.get('dsl') else config_data.get('predict_dsl')
            if not isinstance(inference_dsl, dict):
                inference_dsl = json_loads(inference_dsl)
        else:
            if config_data.get('cpn_list', None):
                cpn_list = config_data.pop('cpn_list')
            else:
                cpn_list = list(train_dsl.get('components', {}).keys())
            if int(dsl_version) == 1:
                # convert v1 dsl to v2 dsl
                inference_dsl, warning_msg = parser.convert_dsl_v1_to_v2(parent_predict_dsl)
            else:
                parser = get_dsl_parser_by_version(dsl_version)
                inference_dsl = parser.deploy_component(cpn_list, train_dsl)

        # convert v1 conf to v2 conf
        if int(dsl_version) == 1:
            components = parser.get_components_light_weight(inference_dsl)

            from fate_flow.db.component_registry import ComponentRegistry
            job_providers = parser.get_job_providers(dsl=inference_dsl, provider_detail=ComponentRegistry.REGISTRY)
            cpn_role_parameters = dict()
            for cpn in components:
                cpn_name = cpn.get_name()
                role_params = parser.parse_component_role_parameters(component=cpn_name,
                                                                     dsl=inference_dsl,
                                                                     runtime_conf=train_runtime_conf,
                                                                     provider_detail=ComponentRegistry.REGISTRY,
                                                                     provider_name=job_providers[cpn_name]["provider"]["name"],
                                                                     provider_version=job_providers[cpn_name]["provider"]["version"])
                cpn_role_parameters[cpn_name] = role_params
            train_runtime_conf = parser.convert_conf_v1_to_v2(train_runtime_conf, cpn_role_parameters)

        adapter = JobRuntimeConfigAdapter(train_runtime_conf)
        train_runtime_conf = adapter.update_model_id_version(model_version=deploy_model.model_version)
        pipeline_model.model_version = child_model_version
        pipeline_model.train_runtime_conf = json_dumps(train_runtime_conf, byte=True)

        #  save inference dsl into child model file
        parser = get_dsl_parser_by_version(2)
        parser.verify_dsl(inference_dsl, "predict")
        inference_dsl = JobSaver.fill_job_inference_dsl(job_id=model_version, role=local_role, party_id=local_party_id, dsl_parser=parser, origin_inference_dsl=inference_dsl)
        pipeline_model.inference_dsl = json_dumps(inference_dsl, byte=True)

        if compare_version(pipeline_model.fate_version, '1.5.0') == 'gt':
            pipeline_model.parent_info = json_dumps({'parent_model_id': model_id, 'parent_model_version': model_version}, byte=True)
            pipeline_model.parent = False
            runtime_conf_on_party['job_parameters']['model_version'] = child_model_version
            pipeline_model.runtime_conf_on_party = json_dumps(runtime_conf_on_party, byte=True)

        # save model file
        deploy_model.save_pipeline(pipeline_model)
        shutil.copyfile(os.path.join(deploy_model.model_path, "pipeline.pb"),
                        os.path.join(deploy_model.model_path, "variables", "data", "pipeline", "pipeline", "Pipeline"))

        model_info = gather_model_info_data(deploy_model)
        model_info['job_id'] = model_info['f_model_version']
        model_info['size'] = deploy_model.calculate_model_file_size()
        model_info['role'] = local_role
        model_info['party_id'] = local_party_id
        model_info['parent'] = False if model_info.get('f_inference_dsl') else True
        if compare_version(model_info['f_fate_version'], '1.5.0') == 'eq':
            model_info['roles'] = model_info.get('f_train_runtime_conf', {}).get('role', {})
            model_info['initiator_role'] = model_info.get('f_train_runtime_conf', {}).get('initiator', {}).get('role')
            model_info['initiator_party_id'] = model_info.get('f_train_runtime_conf', {}).get('initiator', {}).get('party_id')
        save_model_info(model_info)

        for component_name, component in train_dsl.get('components', {}).items():
            step_index = components_checkpoint.get(component_name, {}).get('step_index')
            step_name = components_checkpoint.get(component_name, {}).get('step_name')
            if step_index is not None:
                step_index = int(step_index)
                step_name = None
            elif step_name is None:
                continue

            checkpoint_manager = CheckpointManager(
                role=local_role, party_id=local_party_id,
                model_id=model_id, model_version=model_version,
                component_name=component_name,
                mkdir=False,
            )
            checkpoint_manager.load_checkpoints_from_disk()
            if checkpoint_manager.latest_checkpoint is not None:
                checkpoint_manager.deploy(
                    child_model_version,
                    component['output']['model'][0]
                    if component.get('output', {}).get('model') else 'default',
                    step_index,
                    step_name,
                )
    except Exception as e:
        stat_logger.exception(e)
        return 100, f"deploy model of role {local_role} {local_party_id} failed, details: {str(e)}"
    else:
        msg = f"deploy model of role {local_role} {local_party_id} success"
        if warning_msg:
            msg = msg + f", warning: {warning_msg}"
        return 0, msg
