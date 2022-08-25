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

from fate_arch.common.base_utils import json_loads

from fate_flow.db.db_models import DB, MachineLearningModelInfo as MLModel
from fate_flow.model.sync_model import SyncModel
from fate_flow.pipelined_model.pipelined_model import PipelinedModel
from fate_flow.scheduler.cluster_scheduler import ClusterScheduler
from fate_flow.settings import ENABLE_MODEL_STORE, stat_logger
from fate_flow.utils.base_utils import compare_version, get_fate_flow_directory


def all_party_key(all_party):
    """
    Join all party as party key
    :param all_party:
        "role": {
            "guest": [9999],
            "host": [10000],
            "arbiter": [10000]
         }
    :return:
    """
    if not all_party:
        all_party_key = 'all'
    elif isinstance(all_party, dict):
        sorted_role_name = sorted(all_party.keys())
        all_party_key = '#'.join([
            ('%s-%s' % (
                role_name,
                '_'.join([str(p) for p in sorted(set(all_party[role_name]))]))
             )
            for role_name in sorted_role_name])
    else:
        all_party_key = None
    return all_party_key


def gen_party_model_id(model_id, role, party_id):
    return '#'.join([role, str(party_id), model_id]) if model_id else None


def gen_model_id(all_party):
    return '#'.join([all_party_key(all_party), "model"])


@DB.connection_context()
def query_model_info_from_db(query_filters=None, **kwargs):
    conditions = []
    filters = []

    for k, v in kwargs.items():
        k = f'f_{k}'
        if hasattr(MLModel, k):
            conditions.append(getattr(MLModel, k) == v)

    for k in query_filters:
        k = f'f_{k}'
        if hasattr(MLModel, k):
            filters.append(getattr(MLModel, k))

    models = MLModel.select(*filters)
    if conditions:
        models = models.where(*conditions)
    models = [model.to_dict() for model in models]

    if not models:
        return 100, 'Query model info failed, cannot find model from db.', []
    return 0, 'Query model info from db success.', models


def query_model_info_from_file(model_id='*', model_version='*', role='*', party_id='*', query_filters=None, save_to_db=False, **kwargs):
    fp_list = glob.glob(f"{get_fate_flow_directory('model_local_cache')}/{role}#{party_id}#{model_id}/{model_version}")

    models = []
    for fp in fp_list:
        _, party_model_id, model_version = fp.rsplit('/', 2)
        role, party_id, model_id = party_model_id.split('#', 2)

        pipeline_model = PipelinedModel(model_id=party_model_id, model_version=model_version)
        if not pipeline_model.exists():
            continue

        model_info = gather_model_info_data(pipeline_model)

        if save_to_db:
            try:
                save_model_info(model_info)
            except Exception as e:
                stat_logger.exception(e)

        if query_filters:
            for k, v in model_info.items():
                if k not in query_filters:
                    del model_info[k]

        models.append(model_info)

    if not models:
        return 100, 'Query model info failed, cannot find model from local model files.', []
    return 0, 'Query model info from local model success.', models


def gather_model_info_data(model: PipelinedModel):
    pipeline = model.read_pipeline_model()

    model_info = {}
    for attr, field in pipeline.ListFields():
        if isinstance(field, bytes):
            field = json_loads(field)
        model_info[f'f_{attr.name}'] = field

    model_info['f_job_id'] = model_info['f_model_version']
    model_info['f_role'] = model.role
    model_info['f_party_id'] = model.party_id
    # backward compatibility
    model_info['f_runtime_conf'] = model_info['f_train_runtime_conf']
    model_info['f_size'] = model.calculate_model_file_size()

    if compare_version(model_info['f_fate_version'], '1.5.1') == 'lt':
        model_info['f_roles'] = model_info.get('f_train_runtime_conf', {}).get('role', {})
        model_info['f_initiator_role'] = model_info.get('f_train_runtime_conf', {}).get('initiator', {}).get('role')
        model_info['f_initiator_party_id'] = model_info.get('f_train_runtime_conf', {}).get('initiator', {}).get('party_id')

    return model_info


def query_model_info(**kwargs):
    file_only = kwargs.pop('file_only', False)
    kwargs['query_filters'] = set(kwargs['query_filters']) if kwargs.get('query_filters') else set()

    if not file_only:
        retcode, retmsg, data = query_model_info_from_db(**kwargs)
        if not retcode:
            return retcode, retmsg, data

        kwargs['save_to_db'] = True

    retcode, retmsg, data = query_model_info_from_file(**kwargs)
    if not retcode:
        return retcode, retmsg, data

    return 100, (
        'Query model info failed, cannot find model from db and local model files. '
        'Try use both model id and model version to query model info from local models.'
    ), []


def save_model_info(model_info):
    model_info = {k if k.startswith('f_') else f'f_{k}': v for k, v in model_info.items()}

    with DB.connection_context():
        MLModel.insert(**model_info).on_conflict(preserve=(
            'f_update_time',
            'f_update_date',
            *model_info.keys(),
        )).execute()

    if ENABLE_MODEL_STORE:
        sync_model = SyncModel(
            role=model_info['f_role'], party_id=model_info['f_party_id'],
            model_id=model_info['f_model_id'], model_version=model_info['f_model_version'],
        )
        sync_model.upload(True)

    ClusterScheduler.cluster_command('/model/service/register', {
        'party_model_id': gen_party_model_id(
            model_info['f_model_id'],
            model_info['f_role'],
            model_info['f_party_id'],
        ),
        'model_version': model_info['f_model_version'],
    })


def check_if_parent_model(pipeline):
    if compare_version(pipeline.fate_version, '1.5.0') == 'gt':
        if pipeline.parent:
            return True
    return False


def check_before_deploy(pipeline_model: PipelinedModel):
    pipeline = pipeline_model.read_pipeline_model()

    if compare_version(pipeline.fate_version, '1.5.0') == 'gt':
        if pipeline.parent:
            return True
    elif compare_version(pipeline.fate_version, '1.5.0') == 'eq':
        return True
    return False


def check_if_deployed(role, party_id, model_id, model_version):
    party_model_id = gen_party_model_id(model_id=model_id, role=role, party_id=party_id)
    pipeline_model = PipelinedModel(model_id=party_model_id, model_version=model_version)
    if not pipeline_model.exists():
        raise FileNotFoundError(f"Model {party_model_id} {model_version} not exists in model local cache.")

    pipeline = pipeline_model.read_pipeline_model()
    if compare_version(pipeline.fate_version, '1.5.0') == 'gt':
        train_runtime_conf = json_loads(pipeline.train_runtime_conf)
        if str(train_runtime_conf.get('dsl_version', '1')) != '1':
            if pipeline.parent:
                return False
    return True


@DB.connection_context()
def models_group_by_party_model_id_and_model_version():
    args = [
        MLModel.f_role,
        MLModel.f_party_id,
        MLModel.f_model_id,
        MLModel.f_model_version,
    ]
    return MLModel.select(*args).group_by(*args)


@DB.connection_context()
def get_job_configuration_from_model(job_id, role, party_id):
    retcode, retmsg, data = query_model_info(
        model_version=job_id, role=role, party_id=party_id,
        query_filters=['train_dsl', 'dsl', 'train_runtime_conf', 'runtime_conf'],
    )
    if not data:
        return {}, {}, {}

    dsl = data[0].get('train_dsl') if data[0].get('train_dsl') else data[0].get('dsl')
    runtime_conf = data[0].get('runtime_conf')
    train_runtime_conf = data[0].get('train_runtime_conf')
    return dsl, runtime_conf, train_runtime_conf
