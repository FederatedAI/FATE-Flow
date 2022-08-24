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
import typing
from functools import wraps

from fate_arch.common.base_utils import current_timestamp
from fate_flow.db.db_models import DB, Job
from fate_flow.scheduler.dsl_parser import DSLParserV1, DSLParserV2
from fate_flow.utils.config_adapter import JobRuntimeConfigAdapter
from fate_flow.utils.log_utils import schedule_logger


@DB.connection_context()
def ready_signal(job_id, set_or_reset: bool, ready_timeout_ttl=None):
    filters = [Job.f_job_id == job_id]
    if set_or_reset:
        update_fields = {Job.f_ready_signal: True, Job.f_ready_time: current_timestamp()}
        filters.append(Job.f_ready_signal == False)
    else:
        update_fields = {Job.f_ready_signal: False, Job.f_ready_time: None}
        filters.append(Job.f_ready_signal == True)
        if ready_timeout_ttl:
            filters.append(current_timestamp() - Job.f_ready_time > ready_timeout_ttl)
    update_status = Job.update(update_fields).where(*filters).execute() > 0
    return update_status


@DB.connection_context()
def cancel_signal(job_id, set_or_reset: bool):
    update_status = Job.update({Job.f_cancel_signal: set_or_reset, Job.f_cancel_time: current_timestamp()}).where(Job.f_job_id == job_id).execute() > 0
    return update_status


@DB.connection_context()
def rerun_signal(job_id, set_or_reset: bool):
    if set_or_reset is True:
        update_fields = {Job.f_rerun_signal: True, Job.f_cancel_signal: False, Job.f_end_scheduling_updates: 0}
    elif set_or_reset is False:
        update_fields = {Job.f_rerun_signal: False}
    else:
        raise RuntimeError(f"can not support rereun signal {set_or_reset}")
    update_status = Job.update(update_fields).where(Job.f_job_id == job_id).execute() > 0
    return update_status


def schedule_lock(func):
    @wraps(func)
    def _wrapper(*args, **kwargs):
        _lock = kwargs.pop("lock", False)
        if _lock:
            job = kwargs.get("job")
            schedule_logger(job.f_job_id).info(f"get job {job.f_job_id} schedule lock")
            _result = None
            if not ready_signal(job_id=job.f_job_id, set_or_reset=True):
                schedule_logger(job.f_job_id).info(f"get job {job.f_job_id} schedule lock failed, job may be handled by another scheduler")
                return
            try:
                _result = func(*args, **kwargs)
            except Exception as e:
                raise e
            finally:
                ready_signal(job_id=job.f_job_id, set_or_reset=False)
                schedule_logger(job.f_job_id).info(f"release job {job.f_job_id} schedule lock")
                return _result
        else:
            return func(*args, **kwargs)
    return _wrapper


@DB.connection_context()
def get_job_dsl_parser_by_job_id(job_id):
    jobs = Job.select(Job.f_dsl, Job.f_runtime_conf_on_party, Job.f_train_runtime_conf).where(Job.f_job_id == job_id)
    if jobs:
        job = jobs[0]
        job_dsl_parser = get_job_dsl_parser(dsl=job.f_dsl, runtime_conf=job.f_runtime_conf_on_party,
                                            train_runtime_conf=job.f_train_runtime_conf)
        return job_dsl_parser, job.f_runtime_conf_on_party, job.f_dsl
    else:
        return None, None, None


def get_conf_version(conf: dict):
    return int(conf.get("dsl_version", "1"))


def get_job_dsl_parser(dsl=None, runtime_conf=None, pipeline_dsl=None, train_runtime_conf=None):
    parser_version = get_conf_version(runtime_conf)

    if parser_version == 1:
        dsl, runtime_conf = convert_dsl_and_conf_v1_to_v2(dsl, runtime_conf)
        if pipeline_dsl and train_runtime_conf:
            pipeline_dsl, train_runtime_conf = convert_dsl_and_conf_v1_to_v2(pipeline_dsl, train_runtime_conf)
        parser_version = 2

    dsl_parser = get_dsl_parser_by_version(parser_version)
    job_type = JobRuntimeConfigAdapter(runtime_conf).get_job_type()
    dsl_parser.run(dsl=dsl,
                   runtime_conf=runtime_conf,
                   pipeline_dsl=pipeline_dsl,
                   pipeline_runtime_conf=train_runtime_conf,
                   mode=job_type)
    return dsl_parser


def federated_order_reset(dest_parties, scheduler_partys_info):
    dest_partys_new = []
    scheduler = []
    dest_party_ids_dict = {}
    for dest_role, dest_party_ids in dest_parties:
        from copy import deepcopy
        new_dest_party_ids = deepcopy(dest_party_ids)
        dest_party_ids_dict[dest_role] = new_dest_party_ids
        for scheduler_role, scheduler_party_id in scheduler_partys_info:
            if dest_role == scheduler_role and scheduler_party_id in dest_party_ids:
                dest_party_ids_dict[dest_role].remove(scheduler_party_id)
                scheduler.append((scheduler_role, [scheduler_party_id]))
        if dest_party_ids_dict[dest_role]:
            dest_partys_new.append((dest_role, dest_party_ids_dict[dest_role]))
    if scheduler:
        dest_partys_new.extend(scheduler)
    return dest_partys_new


def get_parser_version_mapping():
    return {
        "1": DSLParserV1(),
        "2": DSLParserV2()
    }


def get_dsl_parser_by_version(version: typing.Union[str, int] = 2):
    mapping = get_parser_version_mapping()
    if isinstance(version, int):
        version = str(version)
    if version not in mapping:
        raise Exception("{} version of dsl parser is not currently supported.".format(version))
    return mapping[version]


def fill_inference_dsl(dsl_parser: DSLParserV2, origin_inference_dsl, components_parameters: dict = None):
    # must fill dsl for fate serving
    if isinstance(dsl_parser, DSLParserV2):
        components_module_name = {}
        for component, param in components_parameters.items():
            components_module_name[component] = param["CodePath"]
        return dsl_parser.get_predict_dsl(predict_dsl=origin_inference_dsl, module_object_dict=components_module_name)
    else:
        raise Exception(f"not support dsl parser {type(dsl_parser)}")


def convert_dsl_and_conf_v1_to_v2(dsl, runtime_conf):
    dsl_parser_v1 = DSLParserV1()
    dsl = dsl_parser_v1.convert_dsl_v1_to_v2(dsl)
    components = dsl_parser_v1.get_components_light_weight(dsl)

    from fate_flow.db.component_registry import ComponentRegistry
    job_providers = dsl_parser_v1.get_job_providers(dsl=dsl, provider_detail=ComponentRegistry.REGISTRY)
    cpn_role_parameters = dict()

    for cpn in components:
        cpn_name = cpn.get_name()
        role_params = dsl_parser_v1.parse_component_role_parameters(
            component=cpn_name, dsl=dsl, runtime_conf=runtime_conf,
            provider_detail=ComponentRegistry.REGISTRY,
            provider_name=job_providers[cpn_name]["provider"]["name"],
            provider_version=job_providers[cpn_name]["provider"]["version"])
        cpn_role_parameters[cpn_name] = role_params
    runtime_conf = dsl_parser_v1.convert_conf_v1_to_v2(runtime_conf, cpn_role_parameters)

    return dsl, runtime_conf
