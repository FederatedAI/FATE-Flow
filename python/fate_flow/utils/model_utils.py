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
import os
from collections import OrderedDict

import peewee

from fate_arch.common.base_utils import current_timestamp, json_loads
from fate_arch.common.conf_utils import get_base_config

from fate_flow.db.db_models import DB
from fate_flow.db.db_models import MachineLearningModelInfo as MLModel
from fate_flow.db.runtime_config import RuntimeConfig
from fate_flow.model.sync_model import SyncModel
from fate_flow.pipelined_model.pipelined_model import PipelinedModel
from fate_flow.settings import HOST, stat_logger
from fate_flow.utils.base_utils import compare_version, get_fate_flow_directory
from fate_flow.utils.log_utils import sql_logger


gen_key_string_separator = '#'


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
        all_party_key = gen_key_string_separator.join([
            ('%s-%s' % (
                role_name,
                '_'.join([str(p) for p in sorted(set(all_party[role_name]))]))
             )
            for role_name in sorted_role_name])
    else:
        all_party_key = None
    return all_party_key


def gen_party_model_id(model_id, role, party_id):
    return gen_key_string_separator.join([role, str(party_id), model_id]) if model_id else None


def gen_model_id(all_party):
    return gen_key_string_separator.join([all_party_key(all_party), "model"])


@DB.connection_context()
def query_model_info_from_db(query_filters=None, **kwargs):
    conditions = []
    filters = []

    for key, val in kwargs.items():
        key = f'f_{key}'
        if hasattr(MLModel, key):
            conditions.append(getattr(MLModel, key) == val)

    if query_filters and isinstance(query_filters, list):
        for key in query_filters:
            key = f'f_{key}'
            if hasattr(MLModel, key):
                filters.append(getattr(MLModel, key))

    models = MLModel.select(*filters)
    if conditions:
        models = models.where(*conditions)

    if not models:
        return 100, 'Query model info failed, cannot find model from db.', []
    return 0, 'Query model info from db success.', [model.to_dict() for model in models]


def query_model_info_from_file(model_id=None, model_version=None, role=None, party_id=None, query_filters=None, to_dict=False, save_to_db=False):
    res = {} if to_dict else []
    model_dir = os.path.join(get_fate_flow_directory(), 'model_local_cache')
    glob_dir = f"{model_dir}{os.sep}{role if role else '*'}#{party_id if party_id else '*'}#{model_id if model_id else '*'}{os.sep}{model_version if model_version else '*'}"
    stat_logger.info(f'glob model dir: {glob_dir}')
    model_fp_list = glob.glob(glob_dir)
    if model_fp_list:
        for fp in model_fp_list:
            pipeline_model = PipelinedModel(model_id=fp.split(os.path.sep)[-2], model_version=fp.split(os.path.sep)[-1])
            model_info = gather_model_info_data(pipeline_model, query_filters=query_filters)
            if model_info:
                local_role = fp.split('/')[-2].split('#')[0]
                local_party_id = fp.split('/')[-2].split('#')[1]
                model_info["f_role"] = local_role
                model_info["f_party_id"] = local_party_id
                if isinstance(res, dict):
                    res[fp] = model_info
                else:
                    res.append(model_info)

                if save_to_db:
                    try:
                        gather_and_save_model_info(pipeline_model, local_role, local_party_id)
                    except Exception as e:
                        stat_logger.exception(e)

    if not res:
        return 100, 'Query model info failed, cannot find model from local model files.', res
    return 0, 'Query model info from local model success.', res


def gather_model_info_data(model: PipelinedModel, query_filters=None):
    if model.exists():
        pipeline = model.read_pipeline_model()
        model_info = OrderedDict()
        if query_filters and isinstance(query_filters, list):
            for attr, field in pipeline.ListFields():
                if attr.name in query_filters:
                    if isinstance(field, bytes):
                        model_info["f_" + attr.name] = json_loads(field, OrderedDict)
                    else:
                        model_info["f_" + attr.name] = field
        else:
            for attr, field in pipeline.ListFields():
                if isinstance(field, bytes):
                    model_info["f_" + attr.name] = json_loads(field, OrderedDict)
                else:
                    model_info["f_" + attr.name] = field
        return model_info
    return []


def query_model_info(**kwargs):
    file_only = kwargs.pop('file_only', False)

    if not file_only:
        retcode, retmsg, data = query_model_info_from_db(**kwargs)
        if not retcode:
            return retcode, retmsg, data

        kwargs['save_to_db'] = True

    retcode, retmsg, data = query_model_info_from_file(**kwargs)
    if not retcode:
        return retcode, retmsg, data

    return 100, 'Query model info failed, cannot find model from db and local model files. ' \
                'Try use both model id and model version to query model info from local models', []


@DB.connection_context()
def save_model_info(model_info):
    model = MLModel()
    model.f_create_time = current_timestamp()
    for k, v in model_info.items():
        attr_name = 'f_%s' % k
        if hasattr(MLModel, attr_name):
            setattr(model, attr_name, v)
        elif hasattr(MLModel, k):
            setattr(model, k, v)

    try:
        rows = model.save(force_insert=True)
        if rows != 1:
            raise Exception("Save to database failed")
    except peewee.IntegrityError as e:
        if e.args[0] != 1062:
            raise Exception("Create {} failed:\n{}".format(MLModel, e))

        sql_logger(job_id=model_info.get("job_id", "fate_flow")).warning(e)
        return
    except Exception as e:
        raise Exception("Create {} failed:\n{}".format(MLModel, e))

    if get_base_config('enable_model_store', False):
        sync_model = SyncModel(
            role=model.f_role, party_id=model.f_party_id,
            model_id=model.f_model_id, model_version=model.f_model_version,
        )
        sync_model.upload(True)

    RuntimeConfig.SERVICE_DB.register_model(gen_party_model_id(
        role=model.f_role, party_id=model.f_party_id, model_id=model.f_model_id
    ), model.f_model_version)

    return model


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
        raise Exception(f"Model {party_model_id} {model_version} not exists in model local cache.")

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
    return MLModel.select(*args).where(MLModel.f_archive_from_ip == HOST).group_by(*args)


@DB.connection_context()
def get_job_configuration_from_model(job_id, role, party_id):
    retcode, retmsg, res = query_model_info(model_version=job_id, role=role, party_id=party_id,
                                            query_filters=['train_dsl', 'dsl', 'train_runtime_conf', 'runtime_conf'])
    if res:
        dsl = res[0].get('train_dsl') if res[0].get('train_dsl') else res[0].get('dsl')
        runtime_conf = res[0].get('runtime_conf')
        train_runtime_conf = res[0].get('train_runtime_conf')
        return dsl, runtime_conf, train_runtime_conf
    return {}, {}, {}


def gather_and_save_model_info(model: PipelinedModel, local_role, local_party_id, **kwargs):
    model_info = gather_model_info_data(model)

    model_info['job_id'] = model_info['f_model_version']
    model_info['size'] = model.calculate_model_file_size()
    model_info['role'] = local_role
    model_info['party_id'] = local_party_id
    model_info['parent'] = False if model_info.get('f_inference_dsl') else True

    if compare_version(model_info['f_fate_version'], '1.5.1') == 'lt':
        model_info['roles'] = model_info.get('f_train_runtime_conf', {}).get('role', {})
        model_info['initiator_role'] = model_info.get('f_train_runtime_conf', {}).get('initiator', {}).get('role')
        model_info['initiator_party_id'] = model_info.get('f_train_runtime_conf', {}).get('initiator', {}).get('party_id')

    model_info.update(kwargs)

    return save_model_info(model_info)
