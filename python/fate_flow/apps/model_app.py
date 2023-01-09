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
import glob
import json
import os
import shutil
import traceback
from copy import deepcopy
from datetime import date, datetime

import peewee
from flask import Response, request, send_file

from fate_arch.common import FederatedMode
from fate_arch.common.base_utils import json_dumps, json_loads
from fate_arch.common.conf_utils import get_base_config
from fate_flow.utils.base_utils import get_fate_flow_directory

from fate_flow.db.db_models import (DB, ModelTag, Tag,
                                    MachineLearningModelInfo as MLModel,
                                    ModelOperationLog as OperLog)
from fate_flow.db.runtime_config import RuntimeConfig
from fate_flow.db.service_registry import ServiceRegistry
from fate_flow.entity import JobConfigurationBase
from fate_flow.entity.types import ModelOperation, TagOperation
from fate_flow.pipelined_model import deploy_model, migrate_model, pipelined_model, publish_model
from fate_flow.scheduler.dag_scheduler import DAGScheduler
from fate_flow.settings import TEMP_DIRECTORY, stat_logger, IS_STANDALONE
from fate_flow.utils import detect_utils, job_utils, model_utils, schedule_utils, api_utils
from fate_flow.utils.api_utils import error_response, federated_api, get_json_result
from fate_flow.utils.config_adapter import JobRuntimeConfigAdapter
from fate_flow.components.model_operation import get_model_storage


@manager.route('/load', methods=['POST'])
def load_model():
    request_config = request.json
    if request_config.get('job_id', None):
        retcode, retmsg, res_data = model_utils.query_model_info(request_config['job_id'], 'guest')
        if res_data:
            model_info = res_data[0]
            request_config['initiator'] = {}
            request_config['initiator']['party_id'] = str(model_info.get('f_initiator_party_id'))
            request_config['initiator']['role'] = model_info.get('f_initiator_role')
            runtime_conf = model_info.get('f_runtime_conf', {}) if model_info.get('f_runtime_conf', {}) else model_info.get('f_train_runtime_conf', {})
            adapter = JobRuntimeConfigAdapter(runtime_conf)
            job_parameters = adapter.get_common_parameters().to_dict()
            request_config['job_parameters'] = job_parameters if job_parameters else model_info.get('f_train_runtime_conf', {}).get('job_parameters')
            roles = runtime_conf.get('role')
            request_config['role'] = roles if roles else model_info.get('f_train_runtime_conf', {}).get('role')
            for key, value in request_config['role'].items():
                for i, v in enumerate(value):
                    value[i] = str(v)
            request_config.pop('job_id')
        else:
            return get_json_result(retcode=101,
                                   retmsg="model with version {} can not be found in database. "
                                          "Please check if the model version is valid.".format(request_config.get('job_id')))
    _job_id = job_utils.generate_job_id()
    initiator_party_id = request_config['initiator']['party_id']
    initiator_role = request_config['initiator']['role']
    publish_model.generate_publish_model_info(request_config)
    load_status = True
    load_status_info = {}
    load_status_msg = 'success'
    load_status_info['detail'] = {}
    if "federated_mode" not in request_config['job_parameters']:
        if IS_STANDALONE:
            request_config['job_parameters']["federated_mode"] = FederatedMode.SINGLE
        else:
            request_config['job_parameters']["federated_mode"] = FederatedMode.MULTIPLE
    for role_name, role_partys in request_config.get("role").items():
        if role_name == 'arbiter':
            continue
        load_status_info[role_name] = load_status_info.get(role_name, {})
        load_status_info['detail'][role_name] = {}
        for _party_id in role_partys:
            request_config['local'] = {'role': role_name, 'party_id': _party_id}
            try:
                response = federated_api(job_id=_job_id,
                                         method='POST',
                                         endpoint='/model/load/do',
                                         src_party_id=initiator_party_id,
                                         dest_party_id=_party_id,
                                         src_role = initiator_role,
                                         json_body=request_config,
                                         federated_mode=request_config['job_parameters']['federated_mode'])
                load_status_info[role_name][_party_id] = response['retcode']
                detail = {_party_id: {}}
                detail[_party_id]['retcode'] = response['retcode']
                detail[_party_id]['retmsg'] = response['retmsg']
                load_status_info['detail'][role_name].update(detail)
                if response['retcode']:
                    load_status = False
                    load_status_msg = 'failed'
            except Exception as e:
                stat_logger.exception(e)
                load_status = False
                load_status_msg = 'failed'
                load_status_info[role_name][_party_id] = 100
    return get_json_result(job_id=_job_id, retcode=(0 if load_status else 101), retmsg=load_status_msg,
                           data=load_status_info)


@manager.route('/migrate', methods=['POST'])
@api_utils.validate_request("migrate_initiator", "role", "migrate_role", "model_id",
                               "model_version", "execute_party", "job_parameters")
def migrate_model_process():
    request_config = request.json
    _job_id = job_utils.generate_job_id()
    initiator_party_id = request_config['migrate_initiator']['party_id']
    initiator_role = request_config['migrate_initiator']['role']
    if not request_config.get("unify_model_version"):
        request_config["unify_model_version"] = _job_id
    migrate_status = True
    migrate_status_info = {}
    migrate_status_msg = 'success'
    migrate_status_info['detail'] = {}

    try:
        if migrate_model.compare_roles(request_config.get("migrate_role"), request_config.get("role")):
            return get_json_result(retcode=100,
                                   retmsg="The config of previous roles is the same with that of migrate roles. "
                                          "There is no need to migrate model. Migration process aborting.")
    except Exception as e:
        return get_json_result(retcode=100, retmsg=str(e))

    local_template = {
        "role": "",
        "party_id": "",
        "migrate_party_id": ""
    }

    res_dict = {}

    for role_name, role_partys in request_config.get("migrate_role").items():
        for offset, party_id in enumerate(role_partys):
            local_res = deepcopy(local_template)
            local_res["role"] = role_name
            local_res["party_id"] = request_config.get("role").get(role_name)[offset]
            local_res["migrate_party_id"] = party_id
            if not res_dict.get(role_name):
                res_dict[role_name] = {}
            res_dict[role_name][local_res["party_id"]] = local_res

    for role_name, role_partys in request_config.get("execute_party").items():
        migrate_status_info[role_name] = migrate_status_info.get(role_name, {})
        migrate_status_info['detail'][role_name] = {}
        for party_id in role_partys:
            request_config["local"] = res_dict.get(role_name).get(party_id)
            try:
                response = federated_api(job_id=_job_id,
                                         method='POST',
                                         endpoint='/model/migrate/do',
                                         src_party_id=initiator_party_id,
                                         dest_party_id=party_id,
                                         src_role=initiator_role,
                                         json_body=request_config,
                                         federated_mode=request_config['job_parameters']['federated_mode'])
                migrate_status_info[role_name][party_id] = response['retcode']
                detail = {party_id: {}}
                detail[party_id]['retcode'] = response['retcode']
                detail[party_id]['retmsg'] = response['retmsg']
                migrate_status_info['detail'][role_name].update(detail)
            except Exception as e:
                stat_logger.exception(e)
                migrate_status = False
                migrate_status_msg = 'failed'
                migrate_status_info[role_name][party_id] = 100
    return get_json_result(job_id=_job_id, retcode=(0 if migrate_status else 101),
                           retmsg=migrate_status_msg, data=migrate_status_info)


@manager.route('/migrate/do', methods=['POST'])
def do_migrate_model():
    request_data = request.json
    retcode, retmsg, data = migrate_model.migration(request_data)
    operation_record(request_data, "migrate", "success" if not retcode else "failed")
    return get_json_result(retcode=retcode, retmsg=retmsg, data=data)


@manager.route('/load/do', methods=['POST'])
def do_load_model():
    request_data = request.json
    request_data['servings'] = RuntimeConfig.SERVICE_DB.get_urls('servings')

    role = request_data['local']['role']
    party_id = request_data['local']['party_id']
    model_id = request_data['job_parameters']['model_id']
    model_version = request_data['job_parameters']['model_version']
    party_model_id = model_utils.gen_party_model_id(model_id, role, party_id)

    if get_base_config('enable_model_store', False):
        pipeline_model = pipelined_model.PipelinedModel(party_model_id, model_version)

        component_parameters = {
            'model_id': party_model_id,
            'model_version': model_version,
            'store_address': ServiceRegistry.MODEL_STORE_ADDRESS,
        }
        model_storage = get_model_storage(component_parameters)

        if pipeline_model.exists() and not model_storage.exists(**component_parameters):
            stat_logger.info(f'Uploading {pipeline_model.model_path} to model storage.')
            model_storage.store(**component_parameters)
        elif not pipeline_model.exists() and model_storage.exists(**component_parameters):
            stat_logger.info(f'Downloading {pipeline_model.model_path} from model storage.')
            model_storage.restore(**component_parameters)

    if not model_utils.check_if_deployed(role, party_id, model_id, model_version):
        return get_json_result(retcode=100,
                               retmsg="Only deployed models could be used to execute process of loading. "
                                      "Please deploy model before loading.")

    retcode, retmsg = publish_model.load_model(request_data)
    try:
        if not retcode:
            with DB.connection_context():
                model = MLModel.get_or_none(MLModel.f_role == request_data["local"]["role"],
                                            MLModel.f_party_id == request_data["local"]["party_id"],
                                            MLModel.f_model_id == request_data["job_parameters"]["model_id"],
                                            MLModel.f_model_version == request_data["job_parameters"]["model_version"])
                if model:
                    model.f_loaded_times += 1
                    model.save()
    except Exception as modify_err:
        stat_logger.exception(modify_err)

    operation_record(request_data, "load", "success" if not retcode else "failed")
    return get_json_result(retcode=retcode, retmsg=retmsg)


@manager.route('/bind', methods=['POST'])
def bind_model_service():
    request_config = request.json
    if request_config.get('job_id', None):
        retcode, retmsg, res_data = model_utils.query_model_info(request_config['job_id'], 'guest')
        if res_data:
            model_info = res_data[0]
            request_config['initiator'] = {}
            request_config['initiator']['party_id'] = str(model_info.get('f_initiator_party_id'))
            request_config['initiator']['role'] = model_info.get('f_initiator_role')

            runtime_conf = model_info.get('f_runtime_conf', {}) if model_info.get('f_runtime_conf', {}) else model_info.get('f_train_runtime_conf', {})
            adapter = JobRuntimeConfigAdapter(runtime_conf)
            job_parameters = adapter.get_common_parameters().to_dict()
            request_config['job_parameters'] = job_parameters if job_parameters else model_info.get('f_train_runtime_conf', {}).get('job_parameters')

            roles = runtime_conf.get('role')
            request_config['role'] = roles if roles else model_info.get('f_train_runtime_conf', {}).get('role')

            for key, value in request_config['role'].items():
                for i, v in enumerate(value):
                    value[i] = str(v)
            request_config.pop('job_id')
        else:
            return get_json_result(retcode=101,
                                   retmsg="model {} can not be found in database. "
                                          "Please check if the model version is valid.".format(request_config.get('job_id')))
    if not request_config.get('servings'):
        # get my party all servings
        request_config['servings'] = RuntimeConfig.SERVICE_DB.get_urls('servings')
    service_id = request_config.get('service_id')
    if not service_id:
        return get_json_result(retcode=101, retmsg='no service id')
    detect_utils.check_config(request_config, ['initiator', 'role', 'job_parameters'])
    bind_status, retmsg = publish_model.bind_model_service(request_config)
    operation_record(request_config, "bind", "success" if not bind_status else "failed")
    return get_json_result(retcode=bind_status, retmsg='service id is {}'.format(service_id) if not retmsg else retmsg)


@manager.route('/transfer', methods=['post'])
def transfer_model():
    party_model_id = request.json.get('namespace')
    model_version = request.json.get('name')
    if not party_model_id or not model_version:
        return error_response(400, 'namespace and name are required')
    model_data = publish_model.download_model(party_model_id, model_version)
    if model_data is None:
        return error_response(404, 'model not found')
    return get_json_result(data=model_data)


@manager.route('/transfer/<party_model_id>/<model_version>', methods=['post'])
def download_model(party_model_id, model_version):
    party_model_id = party_model_id.replace('~', '#')
    model_data = publish_model.download_model(party_model_id, model_version)
    if model_data is None:
        return error_response(404, 'model not found')
    return get_json_result(data=model_data)


@manager.route('/<model_operation>', methods=['post', 'get'])
@api_utils.validate_request("model_id", "model_version", "role", "party_id")
def operate_model(model_operation):
    request_config = request.json or request.form.to_dict()
    job_id = job_utils.generate_job_id()
    if not ModelOperation.valid(model_operation):
        raise Exception('Can not support this operating now: {}'.format(model_operation))
    model_operation = ModelOperation(model_operation)
    request_config["model_id"] = model_utils.gen_party_model_id(
        request_config["model_id"], request_config["role"], request_config["party_id"])
    if model_operation in [ModelOperation.EXPORT, ModelOperation.IMPORT]:
        if model_operation is ModelOperation.IMPORT:
            try:
                file = request.files.get('file')
                file_path = os.path.join(TEMP_DIRECTORY, file.filename)
                # if not os.path.exists(file_path):
                #     raise Exception('The file is obtained from the fate flow client machine, but it does not exist, '
                #                     'please check the path: {}'.format(file_path))
                try:
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    file.save(file_path)
                except Exception as e:
                    shutil.rmtree(file_path)
                    raise e
                request_config['file'] = file_path
                model = pipelined_model.PipelinedModel(request_config["model_id"], request_config["model_version"])
                model.unpack_model(file_path)

                pipeline = model.read_pipeline_model()
                train_runtime_conf = json_loads(pipeline.train_runtime_conf)
                permitted_party_id = []
                for key, value in train_runtime_conf.get('role', {}).items():
                    for v in value:
                        permitted_party_id.extend([v, str(v)])
                if request_config["party_id"] not in permitted_party_id:
                    shutil.rmtree(model.model_path)
                    raise Exception("party id {} is not in model roles, please check if the party id is valid.")
                try:
                    adapter = JobRuntimeConfigAdapter(train_runtime_conf)
                    job_parameters = adapter.get_common_parameters().to_dict()
                    with DB.connection_context():
                        db_model = MLModel.get_or_none(
                            MLModel.f_job_id == job_parameters.get("model_version"),
                            MLModel.f_role == request_config["role"]
                        )
                    if not db_model:
                        model_info = model_utils.gather_model_info_data(model)
                        model_info['imported'] = 1
                        model_info['job_id'] = model_info['f_model_version']
                        model_info['size'] = model.calculate_model_file_size()
                        model_info['role'] = request_config["model_id"].split('#')[0]
                        model_info['party_id'] = request_config["model_id"].split('#')[1]
                        if model_utils.compare_version(model_info['f_fate_version'], '1.5.1') == 'lt':
                            model_info['roles'] = model_info.get('f_train_runtime_conf', {}).get('role', {})
                            model_info['initiator_role'] = model_info.get('f_train_runtime_conf', {}).get('initiator', {}).get('role')
                            model_info['initiator_party_id'] = model_info.get('f_train_runtime_conf', {}).get( 'initiator', {}).get('party_id')
                            model_info['parent'] = False if model_info.get('f_inference_dsl') else True
                        model_utils.save_model_info(model_info)
                    else:
                        stat_logger.info(f'job id: {job_parameters.get("model_version")}, '
                                         f'role: {request_config["role"]} model info already existed in database.')
                except peewee.IntegrityError as e:
                    stat_logger.exception(e)
                operation_record(request_config, "import", "success")
                return get_json_result()
            except Exception:
                operation_record(request_config, "import", "failed")
                raise
        else:
            try:
                model = pipelined_model.PipelinedModel(request_config["model_id"], request_config["model_version"])
                if model.exists():
                    archive_file_path = model.packaging_model()
                    operation_record(request_config, "export", "success")
                    return send_file(archive_file_path, attachment_filename=os.path.basename(archive_file_path), as_attachment=True)

                operation_record(request_config, "export", "failed")
                return error_response(210, f"Model {request_config['model_id']} {request_config['model_version']} is not exist.")
            except Exception as e:
                operation_record(request_config, "export", "failed")
                stat_logger.exception(e)
                return error_response(210, str(e))
    else:
        data = {}
        job_dsl, job_runtime_conf = gen_model_operation_job_config(request_config, model_operation)
        submit_result = DAGScheduler.submit(JobConfigurationBase(**{'dsl': job_dsl, 'runtime_conf': job_runtime_conf}), job_id=job_id)
        data.update(submit_result)
        operation_record(job_runtime_conf, model_operation, '')
        return get_json_result(job_id=job_id, data=data)


@manager.route('/model_tag/<operation>', methods=['POST'])
@DB.connection_context()
def tag_model(operation):
    if operation not in ['retrieve', 'create', 'remove']:
        return get_json_result(retcode=100, retmsg="'{}' is not currently supported.".format(operation))

    request_data = request.json
    model = MLModel.get_or_none(MLModel.f_model_version == request_data.get("job_id"))
    if not model:
        raise Exception("Can not found model by job id: '{}'.".format(request_data.get("job_id")))

    if operation == 'retrieve':
        res = {'tags': []}
        tags = (Tag.select().join(ModelTag, on=ModelTag.f_t_id == Tag.f_id).where(ModelTag.f_m_id == model.f_model_version))
        for tag in tags:
            res['tags'].append({'name': tag.f_name, 'description': tag.f_desc})
        res['count'] = tags.count()
        return get_json_result(data=res)
    elif operation == 'remove':
        tag = Tag.get_or_none(Tag.f_name == request_data.get('tag_name'))
        if not tag:
            raise Exception("Can not found '{}' tag.".format(request_data.get('tag_name')))
        tags = (Tag.select().join(ModelTag, on=ModelTag.f_t_id == Tag.f_id).where(ModelTag.f_m_id == model.f_model_version))
        if tag.f_name not in [t.f_name for t in tags]:
            raise Exception("Model {} {} does not have tag '{}'.".format(model.f_model_id,
                                                                         model.f_model_version,
                                                                         tag.f_name))
        delete_query = ModelTag.delete().where(ModelTag.f_m_id == model.f_model_version, ModelTag.f_t_id == tag.f_id)
        delete_query.execute()
        return get_json_result(retmsg="'{}' tag has been removed from tag list of model {} {}.".format(request_data.get('tag_name'),
                                                                                                       model.f_model_id,
                                                                                                       model.f_model_version))
    else:
        if not str(request_data.get('tag_name')):
            raise Exception("Tag name should not be an empty string.")
        tag = Tag.get_or_none(Tag.f_name == request_data.get('tag_name'))
        if not tag:
            tag = Tag()
            tag.f_name = request_data.get('tag_name')
            tag.save(force_insert=True)
        else:
            tags = (Tag.select().join(ModelTag, on=ModelTag.f_t_id == Tag.f_id).where(ModelTag.f_m_id == model.f_model_version))
            if tag.f_name in [t.f_name for t in tags]:
                raise Exception("Model {} {} already been tagged as tag '{}'.".format(model.f_model_id,
                                                                                      model.f_model_version,
                                                                                      tag.f_name))
        ModelTag.create(f_t_id=tag.f_id, f_m_id=model.f_model_version)
        return get_json_result(retmsg="Adding {} tag for model with job id: {} successfully.".format(request_data.get('tag_name'),
                                                                                                     request_data.get('job_id')))


@manager.route('/tag/<tag_operation>', methods=['POST'])
@DB.connection_context()
def operate_tag(tag_operation):
    request_data = request.json
    if not TagOperation.valid(tag_operation):
        raise Exception('The {} operation is not currently supported.'.format(tag_operation))

    tag_name = request_data.get('tag_name')
    tag_desc = request_data.get('tag_desc')
    tag_operation = TagOperation(tag_operation)
    if tag_operation is TagOperation.CREATE:
        try:
            if not tag_name:
                return get_json_result(retcode=100, retmsg="'{}' tag created failed. Please input a valid tag name.".format(tag_name))
            else:
                Tag.create(f_name=tag_name, f_desc=tag_desc)
        except peewee.IntegrityError:
            raise Exception("'{}' has already exists in database.".format(tag_name))
        else:
            return get_json_result(retmsg="'{}' tag has been created successfully.".format(tag_name))

    elif tag_operation is TagOperation.LIST:
        tags = Tag.select()
        limit = request_data.get('limit')
        res = {"tags": []}

        if limit > len(tags):
            count = len(tags)
        else:
            count = limit
        for tag in tags[:count]:
            res['tags'].append({'name': tag.f_name, 'description': tag.f_desc,
                                'model_count': ModelTag.filter(ModelTag.f_t_id == tag.f_id).count()})
        return get_json_result(data=res)

    else:
        if not (tag_operation is TagOperation.RETRIEVE and not request_data.get('with_model')):
            try:
                tag = Tag.get(Tag.f_name == tag_name)
            except peewee.DoesNotExist:
                raise Exception("Can not found '{}' tag.".format(tag_name))

        if tag_operation is TagOperation.RETRIEVE:
            if request_data.get('with_model', False):
                res = {'models': []}
                models = (MLModel.select().join(ModelTag, on=ModelTag.f_m_id == MLModel.f_model_version).where(ModelTag.f_t_id == tag.f_id))
                for model in models:
                        res["models"].append({
                        "model_id": model.f_model_id,
                        "model_version": model.f_model_version,
                        "model_size": model.f_size,
                        "role": model.f_role,
                        "party_id": model.f_party_id
                    })
                res["count"] = models.count()
                return get_json_result(data=res)
            else:
                tags = Tag.filter(Tag.f_name.contains(tag_name))
                if not tags:
                    return get_json_result(retcode=100, retmsg="No tags found.")
                res = {'tags': []}
                for tag in tags:
                    res['tags'].append({'name': tag.f_name, 'description': tag.f_desc})
                return get_json_result(data=res)

        elif tag_operation is TagOperation.UPDATE:
            new_tag_name = request_data.get('new_tag_name', None)
            new_tag_desc = request_data.get('new_tag_desc', None)
            if (tag.f_name == new_tag_name) and (tag.f_desc == new_tag_desc):
                return get_json_result(100, "Nothing to be updated.")
            else:
                if request_data.get('new_tag_name'):
                    if not Tag.get_or_none(Tag.f_name == new_tag_name):
                        tag.f_name = new_tag_name
                    else:
                        return get_json_result(100, retmsg="'{}' tag already exists.".format(new_tag_name))

                tag.f_desc = new_tag_desc
                tag.save()
                return get_json_result(retmsg="Infomation of '{}' tag has been updated successfully.".format(tag_name))

        else:
            delete_query = ModelTag.delete().where(ModelTag.f_t_id == tag.f_id)
            delete_query.execute()
            Tag.delete_instance(tag)
            return get_json_result(retmsg="'{}' tag has been deleted successfully.".format(tag_name))


def gen_model_operation_job_config(config_data: dict, model_operation: ModelOperation):
    if model_operation not in {ModelOperation.STORE, ModelOperation.RESTORE}:
        raise Exception("Can not support this model operation: {}".format(model_operation))

    component_name = f"{str(model_operation).replace('.', '_').lower()}_0"

    job_dsl = {
        "components": {
            component_name: {
                "module": "Model{}".format(model_operation.value.capitalize()),
            },
        },
    }

    job_runtime_conf = job_utils.runtime_conf_basic(True)

    component_parameters = {
        "model_id": config_data["model_id"],
        "model_version": config_data["model_version"],
        "store_address": ServiceRegistry.MODEL_STORE_ADDRESS,
    }
    if model_operation == ModelOperation.STORE:
        component_parameters["force_update"] = config_data.get("force_update", False)

    job_runtime_conf["component_parameters"]["role"] = {
        "local": {
            "0": {
                component_name: component_parameters,
            },
        },
    }

    return job_dsl, job_runtime_conf


@DB.connection_context()
def operation_record(data: dict, oper_type, oper_status):
    try:
        if oper_type == 'migrate':
            OperLog.create(f_operation_type=oper_type,
                           f_operation_status=oper_status,
                           f_initiator_role=data.get("migrate_initiator", {}).get("role"),
                           f_initiator_party_id=data.get("migrate_initiator", {}).get("party_id"),
                           f_request_ip=request.remote_addr,
                           f_model_id=data.get("model_id"),
                           f_model_version=data.get("model_version"))
        elif oper_type == 'load':
            OperLog.create(f_operation_type=oper_type,
                           f_operation_status=oper_status,
                           f_initiator_role=data.get("initiator").get("role"),
                           f_initiator_party_id=data.get("initiator").get("party_id"),
                           f_request_ip=request.remote_addr,
                           f_model_id=data.get('job_parameters').get("model_id"),
                           f_model_version=data.get('job_parameters').get("model_version"))
        elif oper_type == 'bind':
            OperLog.create(f_operation_type=oper_type,
                           f_operation_status=oper_status,
                           f_initiator_role=data.get("initiator").get("role"),
                           f_initiator_party_id=data.get("party_id") if data.get("party_id") else data.get("initiator").get("party_id"),
                           f_request_ip=request.remote_addr,
                           f_model_id=data.get("model_id") if data.get("model_id") else data.get('job_parameters').get("model_id"),
                           f_model_version=data.get("model_version") if data.get("model_version") else data.get('job_parameters').get("model_version"))
        else:
            OperLog.create(f_operation_type=oper_type,
                           f_operation_status=oper_status,
                           f_initiator_role=data.get("role") if data.get("role") else data.get("initiator").get("role"),
                           f_initiator_party_id=data.get("party_id") if data.get("party_id") else data.get("initiator").get("party_id"),
                           f_request_ip=request.remote_addr,
                           f_model_id=data.get("model_id") if data.get("model_id") else data.get('job_parameters').get("model_id"),
                           f_model_version=data.get("model_version") if data.get("model_version") else data.get('job_parameters').get("model_version"))
    except Exception:
        stat_logger.error(traceback.format_exc())


@manager.route('/query', methods=['POST'])
def query_model():
    retcode, retmsg, data = model_utils.query_model_info(**request.json)
    result = {"retcode": retcode, "retmsg": retmsg, "data": data}
    return Response(json.dumps(result, sort_keys=False, cls=DatetimeEncoder), mimetype="application/json")


@manager.route('/query/detail', methods=['POST'])
def query_model_detail():
    retcode, retmsg, data = model_utils.query_model_detail(**request.json)
    result = {"retcode": retcode, "retmsg": retmsg, "data": data}
    return Response(json.dumps(result, sort_keys=False, cls=DatetimeEncoder), mimetype="application/json")


@manager.route('/deploy', methods=['POST'])
@api_utils.validate_request('model_id', 'model_version')
def deploy():
    request_data = request.json

    model_id = request_data.get("model_id")
    model_version = request_data.get("model_version")

    if not isinstance(request_data.get('components_checkpoint'), dict):
        request_data['components_checkpoint'] = {}

    retcode, retmsg, model_info = model_utils.query_model_info_from_file(model_id, model_version, to_dict=True)
    if not model_info:
        raise Exception(f'Deploy model failed, no model {model_id} {model_version} found.')

    for key, value in model_info.items():
        version_check = model_utils.compare_version(value.get('f_fate_version'), '1.5.0')
        if version_check == 'lt':
            continue

        init_role = key.split('/')[-2].split('#')[0]
        init_party_id = key.split('/')[-2].split('#')[1]
        model_init_role = (value['f_initiator_role'] if value.get('f_initiator_role')
                           else value.get('f_train_runtime_conf', {}).get('initiator', {}).get('role', ''))
        model_init_party_id = (value['f_initiator_party_id'] if value.get('f_initiator_party_id')
                               else value.get('f_train_runtime_conf', {}).get('initiator', {}).get('party_id', ''))

        if init_role == model_init_role and init_party_id == str(model_init_party_id):
            break
    else:
        raise Exception("Deploy model failed, can not found model of initiator role or the fate version of model is older than 1.5.0")

    # distribute federated deploy task
    _job_id = job_utils.generate_job_id()
    request_data['child_model_version'] = _job_id

    initiator_party_id = model_init_party_id
    initiator_role = model_init_role
    request_data['initiator'] = {'role': initiator_role, 'party_id': initiator_party_id}
    deploy_status = True
    deploy_status_info = {}
    deploy_status_msg = 'success'
    deploy_status_info['detail'] = {}

    for role_name, role_partys in value.get("f_train_runtime_conf", {}).get('role', {}).items():
        if role_name not in ['arbiter', 'host', 'guest']:
            continue

        deploy_status_info[role_name] = deploy_status_info.get(role_name, {})
        deploy_status_info['detail'][role_name] = {}
        for _party_id in role_partys:
            request_data['local'] = {'role': role_name, 'party_id': _party_id}
            try:
                response = federated_api(job_id=_job_id,
                                         method='POST',
                                         endpoint='/model/deploy/do',
                                         src_party_id=initiator_party_id,
                                         dest_party_id=_party_id,
                                         src_role=initiator_role,
                                         json_body=request_data,
                                         federated_mode=FederatedMode.MULTIPLE if not IS_STANDALONE else FederatedMode.SINGLE)
                deploy_status_info[role_name][_party_id] = response['retcode']
                detail = {_party_id: {}}
                detail[_party_id]['retcode'] = response['retcode']
                detail[_party_id]['retmsg'] = response['retmsg']
                deploy_status_info['detail'][role_name].update(detail)
                if response['retcode']:
                    deploy_status = False
                    deploy_status_msg = 'failed'
            except Exception as e:
                stat_logger.exception(e)
                deploy_status = False
                deploy_status_msg = 'failed'
                deploy_status_info[role_name][_party_id] = 100

    deploy_status_info['model_id'] = request_data['model_id']
    deploy_status_info['model_version'] = _job_id
    return get_json_result(retcode=(0 if deploy_status else 101),
                           retmsg=deploy_status_msg, data=deploy_status_info)


@manager.route('/deploy/do', methods=['POST'])
def do_deploy():
    retcode, retmsg = deploy_model.deploy(request.json)
    operation_record(request.json, "deploy", "success" if not retcode else "failed")
    return get_json_result(retcode=retcode, retmsg=retmsg)


@manager.route('/get/predict/dsl', methods=['POST'])
def get_predict_dsl():
    request_data = request.json
    request_data['query_filters'] = ['inference_dsl']
    retcode, retmsg, data = model_utils.query_model_info_from_file(**request_data)
    if data:
        for d in data:
            if d.get("f_role") in {"guest", "host"}:
                _data = d
                break
        else:
            return error_response(210, "can not found guest or host model, please get predict dsl on guest or host.")
        if request_data.get("filename"):
            os.makedirs(TEMP_DIRECTORY, exist_ok=True)
            temp_filepath = os.path.join(TEMP_DIRECTORY, request_data.get("filename"))
            with open(temp_filepath, "w") as fout:
                fout.write(json_dumps(_data['f_inference_dsl'], indent=4))
            return send_file(open(temp_filepath, "rb"), as_attachment=True,
                             attachment_filename=request_data.get("filename"))
        else:
            return get_json_result(data=_data['f_inference_dsl'])
    return error_response(210, "No model found, please check if arguments are specified correctly.")


@manager.route('/get/predict/conf', methods=['POST'])
@api_utils.validate_request('model_id', 'model_version')
def get_predict_conf():
    request_data = request.json
    model_dir = os.path.join(get_fate_flow_directory(), 'model_local_cache')
    model_fp_list = glob.glob(model_dir + f"/guest#*#{request_data['model_id']}/{request_data['model_version']}")
    if model_fp_list:
        fp = model_fp_list[0]
        pipeline_model = pipelined_model.PipelinedModel(fp.split('/')[-2], fp.split('/')[-1])
        pipeline = pipeline_model.read_pipeline_model()
        predict_dsl = json_loads(pipeline.inference_dsl)

        train_runtime_conf = json_loads(pipeline.train_runtime_conf)
        parser = schedule_utils.get_dsl_parser_by_version(train_runtime_conf.get('dsl_version', '1') )
        predict_conf = parser.generate_predict_conf_template(predict_dsl, train_runtime_conf,
                                                             request_data['model_id'],
                                                             request_data['model_version'])
    else:
        predict_conf = ''
    if predict_conf:
        if request_data.get("filename"):
            os.makedirs(TEMP_DIRECTORY, exist_ok=True)
            temp_filepath = os.path.join(TEMP_DIRECTORY, request_data.get("filename"))
            with open(temp_filepath, "w") as fout:

                fout.write(json_dumps(predict_conf, indent=4))
            return send_file(open(temp_filepath, "rb"), as_attachment=True,
                             attachment_filename=request_data.get("filename"))
        else:
            return get_json_result(data=predict_conf)
    return error_response(210, "No model found, please check if arguments are specified correctly.")


@manager.route('/homo/convert', methods=['POST'])
@api_utils.validate_request("model_id", "model_version", "role", "party_id")
def homo_convert():
    request_config = request.json or request.form.to_dict()
    retcode, retmsg, res_data = publish_model.convert_homo_model(request_config)
    operation_record(request.json, "homo_convert", "success" if not retcode else "failed")
    return get_json_result(retcode=retcode, retmsg=retmsg, data=res_data)


@manager.route('/homo/deploy', methods=['POST'])
@api_utils.validate_request("service_id", "model_id", "model_version", "role", "party_id",
                            "component_name", "deployment_type", "deployment_parameters")
def homo_deploy():
    request_config = request.json or request.form.to_dict()
    retcode, retmsg, res_data = publish_model.deploy_homo_model(request_config)
    operation_record(request.json, "homo_deploy", "success" if not retcode else "failed")
    return get_json_result(retcode=retcode, retmsg=retmsg, data=res_data)


class DatetimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(obj, date):
            return obj.strftime('%Y-%m-%d')
        else:
            return json.JSONEncoder.default(self, obj)
