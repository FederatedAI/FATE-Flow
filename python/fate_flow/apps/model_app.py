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
from copy import deepcopy
from uuid import uuid1

import peewee
from flask import abort, request, send_file

from fate_arch.common import FederatedMode
from fate_arch.common.base_utils import json_dumps, json_loads

from fate_flow.db.db_models import (
    DB, ModelTag, PipelineComponentMeta, Tag,
    MachineLearningModelInfo as MLModel,
)
from fate_flow.db.runtime_config import RuntimeConfig
from fate_flow.db.service_registry import ServerRegistry
from fate_flow.entity import JobConfigurationBase
from fate_flow.entity.types import ModelOperation, TagOperation
from fate_flow.model.sync_model import SyncComponent, SyncModel
from fate_flow.pipelined_model import deploy_model, migrate_model, publish_model
from fate_flow.pipelined_model.pipelined_model import PipelinedModel
from fate_flow.scheduler.dag_scheduler import DAGScheduler
from fate_flow.settings import ENABLE_MODEL_STORE, IS_STANDALONE, TEMP_DIRECTORY, stat_logger
from fate_flow.utils import detect_utils, job_utils, model_utils
from fate_flow.utils.api_utils import (
    error_response, federated_api, get_json_result,
    send_file_in_mem, validate_request,
)
from fate_flow.utils.base_utils import compare_version
from fate_flow.utils.config_adapter import JobRuntimeConfigAdapter
from fate_flow.utils.job_utils import PIPELINE_COMPONENT_NAME
from fate_flow.utils.schedule_utils import get_dsl_parser_by_version


@manager.route('/load', methods=['POST'])
def load_model():
    request_config = request.json

    if request_config.get('job_id'):
        retcode, retmsg, data = model_utils.query_model_info(model_version=request_config['job_id'], role='guest')
        if not data:
            return get_json_result(
                retcode=101,
                retmsg=f"Model with version {request_config.get('job_id')} can not be found in database. "
                        "Please check if the model version is valid.",
            )

        model_info = data[0]
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
@validate_request("migrate_initiator", "role", "migrate_role", "model_id",
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
    return get_json_result(retcode=retcode, retmsg=retmsg, data=data)


@manager.route('/load/do', methods=['POST'])
def do_load_model():
    request_data = request.json
    request_data['servings'] = RuntimeConfig.SERVICE_DB.get_urls('servings')

    role = request_data['local']['role']
    party_id = request_data['local']['party_id']
    model_id = request_data['job_parameters']['model_id']
    model_version = request_data['job_parameters']['model_version']

    if ENABLE_MODEL_STORE:
        sync_model = SyncModel(
            role=role, party_id=party_id,
            model_id=model_id, model_version=model_version,
        )

        if sync_model.remote_exists():
            sync_model.download(True)

    if not model_utils.check_if_deployed(role, party_id, model_id, model_version):
        return get_json_result(retcode=100,
                               retmsg="Only deployed models could be used to execute process of loading. "
                                      "Please deploy model before loading.")

    retcode, retmsg = publish_model.load_model(request_data)
    try:
        if not retcode:
            with DB.connection_context():
                model = MLModel.get_or_none(
                    MLModel.f_role == role,
                    MLModel.f_party_id == party_id,
                    MLModel.f_model_id == model_id,
                    MLModel.f_model_version == model_version,
                )
                if model:
                    model.f_loaded_times += 1
                    model.save()
    except Exception as modify_err:
        stat_logger.exception(modify_err)

    return get_json_result(retcode=retcode, retmsg=retmsg)


@manager.route('/bind', methods=['POST'])
def bind_model_service():
    request_config = request.json

    if request_config.get('job_id'):
        retcode, retmsg, data = model_utils.query_model_info(model_version=request_config['job_id'], role='guest')
        if not data:
            return get_json_result(
                retcode=101,
                retmsg=f"Model {request_config.get('job_id')} can not be found in database. "
                        "Please check if the model version is valid."
            )

        model_info = data[0]
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

    if not request_config.get('servings'):
        # get my party all servings
        request_config['servings'] = RuntimeConfig.SERVICE_DB.get_urls('servings')
    service_id = request_config.get('service_id')
    if not service_id:
        return get_json_result(retcode=101, retmsg='no service id')
    detect_utils.check_config(request_config, ['initiator', 'role', 'job_parameters'])
    bind_status, retmsg = publish_model.bind_model_service(request_config)

    return get_json_result(retcode=bind_status, retmsg='service id is {}'.format(service_id) if not retmsg else retmsg)


@manager.route('/transfer', methods=['post'])
def transfer_model():
    party_model_id = request.json.get('namespace')
    model_version = request.json.get('name')
    if not party_model_id or not model_version:
        return error_response(400, 'namespace and name are required')
    model_data = publish_model.download_model(party_model_id, model_version)
    if not model_data:
        return error_response(404, 'model not found')
    return get_json_result(data=model_data)


@manager.route('/transfer/<party_model_id>/<model_version>', methods=['post'])
def download_model(party_model_id, model_version):
    party_model_id = party_model_id.replace('~', '#')
    model_data = publish_model.download_model(party_model_id, model_version)
    if not model_data:
        return error_response(404, 'model not found')
    return get_json_result(data=model_data)


@manager.route('/<model_operation>', methods=['post', 'get'])
@validate_request("model_id", "model_version", "role", "party_id")
def operate_model(model_operation):
    request_config = request.json or request.form.to_dict()
    job_id = job_utils.generate_job_id()

    # TODO: export, import, store, restore should NOT be in the same function
    if not ModelOperation.valid(model_operation):
        raise Exception(f'Not supported model operation: "{model_operation}".')
    model_operation = ModelOperation(model_operation)

    request_config['party_id'] = str(request_config['party_id'])
    request_config['model_version'] = str(request_config['model_version'])
    party_model_id = model_utils.gen_party_model_id(
        request_config['model_id'],
        request_config['role'],
        request_config['party_id'],
    )

    if model_operation in [ModelOperation.EXPORT, ModelOperation.IMPORT]:

        if model_operation is ModelOperation.IMPORT:
            file = request.files.get('file')
            if not file:
                return error_response(400, '`file` is required.')

            force_update = bool(int(request_config.get('force_update', 0)))

            if not force_update:
                with DB.connection_context():
                    if MLModel.get_or_none(
                        MLModel.f_role == request_config['role'],
                        MLModel.f_party_id == request_config['party_id'],
                        MLModel.f_model_id == request_config['model_id'],
                        MLModel.f_model_version == request_config['model_version'],
                    ):
                        return error_response(409, 'Model already exists.')

            filename = os.path.join(TEMP_DIRECTORY, uuid1().hex)
            os.makedirs(os.path.dirname(filename), exist_ok=True)

            try:
                file.save(filename)
            except Exception as e:
                try:
                    filename.unlink()
                except FileNotFoundError:
                    pass

                return error_response(500, f'Save file error: {e}')

            model = PipelinedModel(party_model_id, request_config['model_version'])
            model.unpack_model(filename, force_update, request_config.get('hash'))

            pipeline = model.read_pipeline_model()
            train_runtime_conf = json_loads(pipeline.train_runtime_conf)

            for _party_id in train_runtime_conf['role'].get(request_config['role'], []):
                if request_config['party_id'] == str(_party_id):
                    break
            else:
                shutil.rmtree(model.model_path, ignore_errors=True)
                return error_response(
                    400,
                    f'Party id "{request_config["party_id"]}" is not in role "{request_config["role"]}", '
                    f'please check if the party id and role is valid.',
                )

            model.pipelined_component.save_define_meta_from_file_to_db(force_update)

            if ENABLE_MODEL_STORE:
                query = model.pipelined_component.get_define_meta_from_db(
                    PipelineComponentMeta.f_component_name != PIPELINE_COMPONENT_NAME,
                )
                for row in query:
                    sync_component = SyncComponent(
                        role=request_config['role'], party_id=request_config['party_id'],
                        model_id=request_config['model_id'], model_version=request_config['model_version'],
                        component_name=row.f_component_name,
                    )
                    sync_component.upload()

            pipeline.model_id = request_config['model_id']
            pipeline.model_version = request_config['model_version']

            train_runtime_conf = JobRuntimeConfigAdapter(
                train_runtime_conf,
            ).update_model_id_version(
                model_id=request_config['model_id'],
                model_version=request_config['model_version'],
            )

            if compare_version(pipeline.fate_version, '1.5.0') == 'gt':
                runtime_conf_on_party = json_loads(pipeline.runtime_conf_on_party)
                runtime_conf_on_party['job_parameters']['model_id'] = request_config['model_id']
                runtime_conf_on_party['job_parameters']['model_version'] = request_config['model_version']

                # fix migrate bug between 1.5.x and 1.8.x
                if compare_version(pipeline.fate_version, '1.9.0') == 'lt':
                    pipeline.roles = json_dumps(train_runtime_conf['role'], byte=True)

                    runtime_conf_on_party['role'] = train_runtime_conf['role']
                    runtime_conf_on_party['initiator'] = train_runtime_conf['initiator']

                pipeline.runtime_conf_on_party = json_dumps(runtime_conf_on_party, byte=True)

            model.save_pipeline_model(pipeline, False)

            model_info = model_utils.gather_model_info_data(model)
            model_info['f_role'] = request_config['role']
            model_info['f_party_id'] = request_config['party_id']
            model_info['f_job_id'] = job_id
            model_info['f_imported'] = 1
            model_utils.save_model_info(model_info)

            return get_json_result(data={
                'job_id': job_id,
                'role': request_config['role'],
                'party_id': request_config['party_id'],
                'model_id': request_config['model_id'],
                'model_version': request_config['model_version'],
            })

        # export
        else:
            if ENABLE_MODEL_STORE:
                sync_model = SyncModel(
                    role=request_config['role'], party_id=request_config['party_id'],
                    model_id=request_config['model_id'], model_version=request_config['model_version'],
                )
                if sync_model.remote_exists():
                    sync_model.download(True)

            model = PipelinedModel(party_model_id, request_config["model_version"])
            if not model.exists():
                return error_response(404, f"Model {party_model_id} {request_config['model_version']} does not exist.")

            model.packaging_model()
            return send_file(
                model.archive_model_file_path,
                as_attachment=True,
                attachment_filename=os.path.basename(model.archive_model_file_path),
            )

    # store and restore
    else:
        request_config['model_id'] = party_model_id

        job_dsl, job_runtime_conf = gen_model_operation_job_config(request_config, model_operation)
        submit_result = DAGScheduler.submit(JobConfigurationBase(**{'dsl': job_dsl, 'runtime_conf': job_runtime_conf}), job_id=job_id)

        return get_json_result(job_id=job_id, data=submit_result)


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
        "store_address": ServerRegistry.MODEL_STORE_ADDRESS,
    }
    if model_operation == ModelOperation.STORE:
        component_parameters["force_update"] = config_data.get("force_update", False)
    elif model_operation == ModelOperation.RESTORE:
        component_parameters["hash_"] = config_data.get("sha256", None)

    job_runtime_conf["component_parameters"]["role"] = {
        "local": {
            "0": {
                component_name: component_parameters,
            },
        },
    }

    return job_dsl, job_runtime_conf


@manager.route('/query', methods=['POST'])
def query_model():
    request_data = request.json or request.form.to_dict() or {}

    retcode, retmsg, data = model_utils.query_model_info(**request_data)
    return get_json_result(retcode=retcode, retmsg=retmsg, data=data)


@manager.route('/deploy', methods=['POST'])
@validate_request('model_id', 'model_version')
def deploy():
    request_data = request.json

    model_id = request_data['model_id']
    model_version = request_data['model_version']

    if not isinstance(request_data.get('components_checkpoint'), dict):
        request_data['components_checkpoint'] = {}

    retcode, retmsg, data = model_utils.query_model_info(model_id=model_id, model_version=model_version)
    if not data:
        return error_response(
            404,
             'Deploy model failed. '
            f'Model {model_id} {model_version} not found.'
        )

    for model_info in data:
        version_check = compare_version(model_info.get('f_fate_version'), '1.5.0')
        if version_check == 'lt':
            continue

        initiator_role = (model_info['f_initiator_role'] if model_info.get('f_initiator_role')
                          else model_info.get('f_train_runtime_conf', {}).get('initiator', {}).get('role', ''))
        initiator_party_id = (model_info['f_initiator_party_id'] if model_info.get('f_initiator_party_id')
                              else model_info.get('f_train_runtime_conf', {}).get('initiator', {}).get('party_id', ''))

        if model_info['f_role']  == initiator_role and str(model_info['f_party_id']) == str(initiator_party_id):
            break
    else:
        return error_response(
            404,
            'Deploy model failed. '
            'Cannot found model of initiator role or the fate version of model is older than 1.5.0',
        )

    roles = (
        data[0].get('f_roles') or
        data[0].get('f_train_runtime_conf', {}).get('role') or
        data[0].get('f_runtime_conf', {}).get('role')
    )
    if not roles:
        return error_response(
            404,
            'Deploy model failed. '
            'Cannot found roles of model.'
        )

    # distribute federated deploy task
    _job_id = job_utils.generate_job_id()
    request_data['child_model_version'] = _job_id
    request_data['initiator'] = {
        'role': initiator_role,
        'party_id': initiator_party_id,
    }

    deploy_status = True
    deploy_status_info = {
        'detail': {},
        'model_id': model_id,
        'model_version': _job_id,
    }

    for role_name, role_partys in roles.items():
        if role_name not in {'arbiter', 'host', 'guest'}:
            continue

        if role_name not in deploy_status_info:
            deploy_status_info[role_name] = {}
        if role_name not in deploy_status_info['detail']:
            deploy_status_info['detail'][role_name] = {}

        for _party_id in role_partys:
            request_data['local'] = {
                'role': role_name,
                'party_id': _party_id,
            }

            try:
                response = federated_api(
                    job_id=_job_id,
                    method='POST',
                    endpoint='/model/deploy/do',
                    src_party_id=initiator_party_id,
                    dest_party_id=_party_id,
                    src_role=initiator_role,
                    json_body=request_data,
                    federated_mode=FederatedMode.MULTIPLE if not IS_STANDALONE else FederatedMode.SINGLE
                )
                if response['retcode']:
                    deploy_status = False

                deploy_status_info[role_name][_party_id] = response['retcode']
                deploy_status_info['detail'][role_name][_party_id] = {
                    'retcode': response['retcode'],
                    'retmsg': response['retmsg'],
                }
            except Exception as e:
                deploy_status = False

                deploy_status_info[role_name][_party_id] = 100
                deploy_status_info['detail'][role_name][_party_id] = {
                    'retcode': 100,
                    'retmsg': 'request failed',
                }

                stat_logger.exception(e)

    return get_json_result(
        0 if deploy_status else 101,
        'success' if deploy_status else 'failed',
        deploy_status_info,
    )


@manager.route('/deploy/do', methods=['POST'])
def do_deploy():
    retcode, retmsg = deploy_model.deploy(request.json)

    return get_json_result(retcode=retcode, retmsg=retmsg)


def get_dsl_and_conf():
    request_data = request.json or request.form.to_dict() or {}
    request_data['query_filters'] = [
        'model_id',
        'model_version',
        'role',
        'party_id',
        'train_runtime_conf',
        'inference_dsl',
    ]

    retcode, retmsg, data = model_utils.query_model_info(**request_data)

    if not data:
        abort(error_response(
            210,
            'No model found, '
            'please check if arguments are specified correctly.',
        ))

    for _data in data:
        if _data.get('f_role') in {'guest', 'host'}:
            data = _data
            break
    else:
        abort(error_response(
            210,
            'Cannot found guest or host model, '
            'please get predict dsl on guest or host.',
        ))

    return request_data, data


@manager.route('/get/predict/dsl', methods=['POST'])
def get_predict_dsl():
    request_data, data = get_dsl_and_conf()

    if request_data.get('filename'):
        return send_file_in_mem(data['f_inference_dsl'], request_data['filename'])

    return get_json_result(data=data['f_inference_dsl'])


@manager.route('/get/predict/conf', methods=['POST'])
def get_predict_conf():
    request_data, data = get_dsl_and_conf()

    parser = get_dsl_parser_by_version(data['f_train_runtime_conf'].get('dsl_version', 1))
    conf = parser.generate_predict_conf_template(
        data['f_inference_dsl'], data['f_train_runtime_conf'],
        data['f_model_id'], data['f_model_version'],
    )

    if request_data.get('filename'):
        return send_file_in_mem(conf, request_data['filename'])

    return get_json_result(data=conf)


@manager.route('/archive/packaging', methods=['POST'])
@validate_request('party_model_id', 'model_version')
def packaging_model():
    request_data = request.json or request.form.to_dict()

    if ENABLE_MODEL_STORE:
        sync_model = SyncModel(
            party_model_id=request_data['party_model_id'],
            model_version=request_data['model_version'],
        )
        if sync_model.remote_exists():
            sync_model.download(True)

    model = PipelinedModel(
        model_id=request_data['party_model_id'],
        model_version=request_data['model_version'],
    )

    if not model.exists():
        return error_response(404, 'Model not found.')

    hash_ = model.packaging_model()

    return get_json_result(data={
        'party_model_id': model.party_model_id,
        'model_version': model.model_version,
        'path': model.archive_model_file_path,
        'hash': hash_,
    })


@manager.route('/service/register', methods=['POST'])
@validate_request('party_model_id', 'model_version')
def register_service():
    request_data = request.json or request.form.to_dict()

    RuntimeConfig.SERVICE_DB.register_model(
        party_model_id=request_data['party_model_id'],
        model_version=request_data['model_version'],
    )

    return get_json_result(data={
        'party_model_id': request_data['party_model_id'],
        'model_version': request_data['model_version'],
    })


@manager.route('/homo/convert', methods=['POST'])
@validate_request("model_id", "model_version", "role", "party_id")
def homo_convert():
    request_data = request.json or request.form.to_dict()
    retcode, retmsg, res_data = publish_model.convert_homo_model(request_data)

    return get_json_result(retcode=retcode, retmsg=retmsg, data=res_data)


@manager.route('/homo/deploy', methods=['POST'])
@validate_request("service_id", "model_id", "model_version", "role", "party_id",
                  "component_name", "deployment_type", "deployment_parameters")
def homo_deploy():
    request_data = request.json or request.form.to_dict()
    retcode, retmsg, res_data = publish_model.deploy_homo_model(request_data)

    return get_json_result(retcode=retcode, retmsg=retmsg, data=res_data)
