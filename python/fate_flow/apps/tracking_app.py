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
import json
import os

from flask import request, send_file, jsonify

from fate_flow.component_env_utils.env_utils import import_component_output_depend
from fate_flow.db.db_models import Job, DB
from fate_flow.manager.data_manager import delete_metric_data, TableStorage, get_component_output_data_schema
from fate_flow.operation.job_tracker import Tracker
from fate_flow.operation.job_saver import JobSaver
from fate_flow.scheduler.federated_scheduler import FederatedScheduler
from fate_flow.settings import stat_logger, TEMP_DIRECTORY
from fate_flow.utils import job_utils, schedule_utils, model_utils
from fate_flow.utils.api_utils import get_json_result, error_response
from fate_flow.utils.config_adapter import JobRuntimeConfigAdapter
from fate_flow.utils.detect_utils import validate_request
from fate_flow.component_env_utils import feature_utils


@manager.route('/job/data_view', methods=['post'])
def job_view():
    request_data = request.json
    check_request_parameters(request_data)
    job_tracker = Tracker(job_id=request_data['job_id'], role=request_data['role'], party_id=request_data['party_id'])
    job_view_data = job_tracker.get_job_view()
    if job_view_data:
        job_metric_list = job_tracker.get_metric_list(job_level=True)
        job_view_data['model_summary'] = {}
        for metric_namespace, namespace_metrics in job_metric_list.items():
            job_view_data['model_summary'][metric_namespace] = job_view_data['model_summary'].get(metric_namespace, {})
            for metric_name in namespace_metrics:
                job_view_data['model_summary'][metric_namespace][metric_name] = job_view_data['model_summary'][
                    metric_namespace].get(metric_name, {})
                for metric_data in job_tracker.get_job_metric_data(metric_namespace=metric_namespace,
                                                                   metric_name=metric_name):
                    job_view_data['model_summary'][metric_namespace][metric_name][metric_data.key] = metric_data.value
        return get_json_result(retcode=0, retmsg='success', data=job_view_data)
    else:
        return get_json_result(retcode=101, retmsg='error')


@manager.route('/component/metric/all', methods=['post'])
def component_metric_all():
    request_data = request.json
    check_request_parameters(request_data)
    tracker = Tracker(job_id=request_data['job_id'], component_name=request_data['component_name'],
                      role=request_data['role'], party_id=request_data['party_id'])
    metrics = tracker.get_metric_list()
    all_metric_data = {}
    if metrics:
        for metric_namespace, metric_names in metrics.items():
            all_metric_data[metric_namespace] = all_metric_data.get(metric_namespace, {})
            for metric_name in metric_names:
                all_metric_data[metric_namespace][metric_name] = all_metric_data[metric_namespace].get(metric_name, {})
                metric_data, metric_meta = get_metric_all_data(tracker=tracker, metric_namespace=metric_namespace,
                                                               metric_name=metric_name)
                all_metric_data[metric_namespace][metric_name]['data'] = metric_data
                all_metric_data[metric_namespace][metric_name]['meta'] = metric_meta
        return get_json_result(retcode=0, retmsg='success', data=all_metric_data)
    else:
        return get_json_result(retcode=0, retmsg='no data', data={})


@manager.route('/component/metrics', methods=['post'])
def component_metrics():
    request_data = request.json
    check_request_parameters(request_data)
    tracker = Tracker(job_id=request_data['job_id'], component_name=request_data['component_name'],
                      role=request_data['role'], party_id=request_data['party_id'])
    metrics = tracker.get_metric_list()
    if metrics:
        return get_json_result(retcode=0, retmsg='success', data=metrics)
    else:
        return get_json_result(retcode=0, retmsg='no data', data={})


@manager.route('/component/metric_data', methods=['post'])
def component_metric_data():
    request_data = request.json
    check_request_parameters(request_data)
    tracker = Tracker(job_id=request_data['job_id'], component_name=request_data['component_name'],
                      role=request_data['role'], party_id=request_data['party_id'])
    metric_data, metric_meta = get_metric_all_data(tracker=tracker, metric_namespace=request_data['metric_namespace'],
                                                   metric_name=request_data['metric_name'])
    if metric_data or metric_meta:
        return get_json_result(retcode=0, retmsg='success', data=metric_data,
                               meta=metric_meta)
    else:
        return get_json_result(retcode=0, retmsg='no data', data=[], meta={})


def get_metric_all_data(tracker, metric_namespace, metric_name):
    metric_data = tracker.get_metric_data(metric_namespace=metric_namespace,
                                          metric_name=metric_name)
    metric_meta = tracker.get_metric_meta(metric_namespace=metric_namespace,
                                          metric_name=metric_name)
    if metric_data or metric_meta:
        metric_data_list = [(metric.key, metric.value) for metric in metric_data]
        metric_data_list.sort(key=lambda x: x[0])
        return metric_data_list, metric_meta.to_dict() if metric_meta else {}
    else:
        return [], {}


@manager.route('/component/metric/delete', methods=['post'])
def component_metric_delete():
    sql = delete_metric_data(request.json)
    return get_json_result(retcode=0, retmsg='success', data=sql)


@manager.route('/component/parameters', methods=['post'])
def component_parameters():
    request_data = request.json
    check_request_parameters(request_data)
    tasks = JobSaver.query_task(only_latest=True, **request_data)
    if not tasks:
        return get_json_result(retcode=101, retmsg='can not found this task')
    parameters = tasks[0].f_component_parameters
    output_parameters = {}
    output_parameters['module'] = parameters.get('module', '')
    for p_k, p_v in parameters.items():
        if p_k.endswith('Param'):
            output_parameters[p_k] = p_v
    return get_json_result(retcode=0, retmsg='success', data=output_parameters)


@manager.route('/component/output/model', methods=['post'])
def component_output_model():
    request_data = request.json
    check_request_parameters(request_data)
    job_configuration = job_utils.get_job_configuration(job_id=request_data['job_id'],
                                                        role=request_data['role'],
                                                        party_id=request_data['party_id'])
    job_dsl, job_runtime_conf, train_runtime_conf = job_configuration.dsl, job_configuration.runtime_conf, job_configuration.train_runtime_conf

    try:
        model_id = job_configuration.runtime_conf_on_party['job_parameters']['model_id']
        model_version = job_configuration.runtime_conf_on_party['job_parameters']['model_version']
    except Exception as e:
        job_dsl, job_runtime_conf, train_runtime_conf = model_utils.get_job_configuration_from_model(job_id=request_data['job_id'],
                                                                                                     role=request_data['role'],
                                                                                                     party_id=request_data['party_id'])
        if any([job_dsl, job_runtime_conf, train_runtime_conf]):
            adapter = JobRuntimeConfigAdapter(job_runtime_conf)
            model_id = adapter.get_common_parameters().to_dict().get('model_id')
            model_version = adapter.get_common_parameters().to_dict.get('model_version')
        else:
            stat_logger.exception(e)
            stat_logger.error(f"Can not find model info by filters: job id: {request_data.get('job_id')}, "
                              f"role: {request_data.get('role')}, party id: {request_data.get('party_id')}")
            raise Exception(f"Can not find model info by filters: job id: {request_data.get('job_id')}, "
                            f"role: {request_data.get('role')}, party id: {request_data.get('party_id')}")

    tracker = Tracker(job_id=request_data['job_id'], component_name=request_data['component_name'],
                      role=request_data['role'], party_id=request_data['party_id'], model_id=model_id,
                      model_version=model_version)
    dsl_parser = schedule_utils.get_job_dsl_parser(dsl=job_dsl, runtime_conf=job_runtime_conf,
                                                   train_runtime_conf=train_runtime_conf)
    component = dsl_parser.get_component_info(request_data['component_name'])
    output_model_json = {}
    # There is only one model output at the current dsl version.
    output_model = tracker.get_output_model(component.get_output()['model'][0] if component.get_output().get('model') else 'default', output_json=True)
    for buffer_name, buffer_object_json_format in output_model.items():
        if buffer_name.endswith('Param'):
            output_model_json = buffer_object_json_format
    if output_model_json:
        component_define = tracker.get_component_define()
        this_component_model_meta = {}
        for buffer_name, buffer_object_json_format in output_model.items():
            if buffer_name.endswith('Meta'):
                this_component_model_meta['meta_data'] = buffer_object_json_format
        this_component_model_meta.update(component_define)
        return get_json_result(retcode=0, retmsg='success', data=output_model_json, meta=this_component_model_meta)
    else:
        return get_json_result(retcode=0, retmsg='no data', data={})


@manager.route('/component/output/data', methods=['post'])
def component_output_data():
    request_data = request.json
    tasks = JobSaver.query_task(only_latest=True, job_id=request_data['job_id'],
                                component_name=request_data['component_name'],
                                role=request_data['role'], party_id=request_data['party_id'])
    if not tasks:
        raise ValueError(f'no found task, please check if the parameters are correct:{request_data}')
    import_component_output_depend(tasks[0].f_provider_info)
    output_tables_meta = get_component_output_tables_meta(task_data=request_data)
    if not output_tables_meta:
        return get_json_result(retcode=0, retmsg='no data', data=[])
    output_data_list = []
    headers = []
    totals = []
    data_names = []
    for output_name, output_table_meta in output_tables_meta.items():
        output_data = []
        is_str = False
        if output_table_meta:
            for k, v in output_table_meta.get_part_of_data():
                data_line, is_str, extend_header = feature_utils.get_component_output_data_line(src_key=k, src_value=v, schema=output_table_meta.get_schema())
                output_data.append(data_line)
            total = output_table_meta.get_count()
            output_data_list.append(output_data)
            data_names.append(output_name)
            totals.append(total)
        if output_data:
            header = get_component_output_data_schema(output_table_meta=output_table_meta, is_str=is_str,
                                                      extend_header=extend_header)
            headers.append(header)
        else:
            headers.append(None)
    if len(output_data_list) == 1 and not output_data_list[0]:
        return get_json_result(retcode=0, retmsg='no data', data=[])
    return get_json_result(retcode=0, retmsg='success', data=output_data_list,
                           meta={'header': headers, 'total': totals, 'names': data_names})


@manager.route('/component/output/data/download', methods=['get'])
def component_output_data_download():
    request_data = request.json
    tasks = JobSaver.query_task(only_latest=True, job_id=request_data['job_id'],
                                component_name=request_data['component_name'],
                                role=request_data['role'], party_id=request_data['party_id'])
    if not tasks:
        raise ValueError(f'no found task, please check if the parameters are correct:{request_data}')
    import_component_output_depend(tasks[0].f_provider_info)
    try:
        output_tables_meta = get_component_output_tables_meta(task_data=request_data)
    except Exception as e:
        stat_logger.exception(e)
        return error_response(210, str(e))
    limit = request_data.get('limit', -1)
    if not output_tables_meta:
        return error_response(response_code=210, retmsg='no data')
    if limit == 0:
        return error_response(response_code=210, retmsg='limit is 0')
    tar_file_name = 'job_{}_{}_{}_{}_output_data.tar.gz'.format(request_data['job_id'],
                                                                request_data['component_name'],
                                                                request_data['role'], request_data['party_id'])
    return TableStorage.send_table(output_tables_meta, tar_file_name, limit=limit, need_head=request_data.get("head", True))


@manager.route('/component/output/data/table', methods=['post'])
@validate_request('job_id', 'role', 'party_id', 'component_name')
def component_output_data_table():
    request_data = request.json
    jobs = JobSaver.query_job(job_id=request_data.get('job_id'))
    if jobs:
        job = jobs[0]
        return jsonify(FederatedScheduler.tracker_command(job, request_data, 'output/table'))
    else:
        return get_json_result(retcode=100, retmsg='No found job')


@manager.route('/component/summary/download', methods=['POST'])
@validate_request("job_id", "component_name", "role", "party_id")
def get_component_summary():
    request_data = request.json
    try:
        tracker = Tracker(job_id=request_data["job_id"], component_name=request_data["component_name"],
                          role=request_data["role"], party_id=request_data["party_id"],
                          task_id=request_data.get("task_id", None), task_version=request_data.get("task_version", None))
        summary = tracker.read_summary_from_db()
        if summary:
            if request_data.get("filename"):
                temp_filepath = os.path.join(TEMP_DIRECTORY, request_data.get("filename"))
                with open(temp_filepath, "w") as fout:
                    fout.write(json.dumps(summary, indent=4))
                return send_file(open(temp_filepath, "rb"), as_attachment=True,
                                 attachment_filename=request_data.get("filename"))
            else:
                return get_json_result(data=summary)
        return error_response(210, "No component summary found, please check if arguments are specified correctly.")
    except Exception as e:
        stat_logger.exception(e)
        return error_response(210, str(e))


@manager.route('/component/list', methods=['POST'])
def component_list():
    request_data = request.json
    parser = schedule_utils.get_job_dsl_parser_by_job_id(job_id=request_data.get('job_id'))
    if parser:
        return get_json_result(data={'components': list(parser.get_dsl().get('components').keys())})
    else:
        return get_json_result(retcode=100, retmsg='No job matched, please make sure the job id is valid.')


def get_component_output_tables_meta(task_data):
    check_request_parameters(task_data)
    tracker = Tracker(job_id=task_data['job_id'], component_name=task_data['component_name'],
                      role=task_data['role'], party_id=task_data['party_id'])
    output_data_table_infos = tracker.get_output_data_info()
    output_tables_meta = tracker.get_output_data_table(output_data_infos=output_data_table_infos)
    return output_tables_meta


# def get_component_output_data_line(src_key, src_value):
#     data_line = [src_key]
#     is_str = False
#     extend_header = []
#     if hasattr(src_value, "is_instance"):
#         for inst in ["inst_id", "label", "weight"]:
#             if getattr(src_value, inst) is not None:
#                 data_line.append(getattr(src_value, inst))
#                 extend_header.append(inst)
#         data_line.extend(feature_utils.dataset_to_list(src_value.features))
#     elif isinstance(src_value, str):
#         data_line.extend([value for value in src_value.split(',')])
#         is_str = True
#     else:
#         data_line.extend(feature_utils.dataset_to_list(src_value))
#     return data_line, is_str, extend_header


@DB.connection_context()
def check_request_parameters(request_data):
    if 'role' not in request_data and 'party_id' not in request_data:
        jobs = Job.select(Job.f_runtime_conf_on_party).where(Job.f_job_id == request_data.get('job_id', ''),
                                                             Job.f_is_initiator == True)
        if jobs:
            job = jobs[0]
            job_runtime_conf = job.f_runtime_conf_on_party
            job_initiator = job_runtime_conf.get('initiator', {})
            role = job_initiator.get('role', '')
            party_id = job_initiator.get('party_id', 0)
            request_data['role'] = role
            request_data['party_id'] = party_id
