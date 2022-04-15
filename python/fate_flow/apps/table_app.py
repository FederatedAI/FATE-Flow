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
from fate_arch import storage
from fate_arch.metastore.db_utils import StorageConnector
from fate_arch.session import Session
from fate_arch.storage import StorageTableMeta, StorageTableOrigin
from fate_flow.entity import RunParameters
from fate_flow.manager.data_manager import DataTableTracker, TableStorage
from fate_flow.operation.job_saver import JobSaver
from fate_flow.operation.job_tracker import Tracker
from fate_flow.worker.task_executor import TaskExecutor
from fate_flow.utils.api_utils import get_json_result, error_response
from fate_flow.utils import job_utils, schedule_utils
from flask import request
from fate_flow.utils.detect_utils import validate_request


@manager.route('/connector/create', methods=['POST'])
def create_storage_connector():
    request_data = request.json
    address = StorageTableMeta.create_address(request_data.get("engine"), request_data.get("connector_info"))
    connector = StorageConnector(connector_name=request_data.get("connector_name"), engine=request_data.get("engine"),
                                 connector_info=address.connector)
    connector.create_or_update()
    return get_json_result(retcode=0, retmsg='success')


@manager.route('/connector/query', methods=['POST'])
def query_storage_connector():
    request_data = request.json
    connector = StorageConnector(connector_name=request_data.get("connector_name"))
    return get_json_result(retcode=0, retmsg='success', data=connector.get_info())


@manager.route('/add', methods=['post'])
@manager.route('/bind', methods=['post'])
@validate_request("engine", "address", "namespace", "name")
def table_bind():
    request_data = request.json
    address_dict = request_data.get('address')
    engine = request_data.get('engine')
    name = request_data.get('name')
    namespace = request_data.get('namespace')
    address = storage.StorageTableMeta.create_address(storage_engine=engine, address_dict=address_dict)
    in_serialized = request_data.get("in_serialized", 1 if engine in {storage.StorageEngine.STANDALONE, storage.StorageEngine.EGGROLL,
                                                                      storage.StorageEngine.MYSQL, storage.StorageEngine.PATH} else 0)
    destroy = (int(request_data.get("drop", 0)) == 1)
    data_table_meta = storage.StorageTableMeta(name=name, namespace=namespace)
    if data_table_meta:
        if destroy:
            data_table_meta.destroy_metas()
        else:
            return get_json_result(retcode=100,
                                   retmsg='The data table already exists.'
                                          'If you still want to continue uploading, please add the parameter --drop')
    id_column = request_data.get("id_column") or request_data.get("id_name")
    feature_column = request_data.get("feature_column") or request_data.get("feature_name")
    schema = None
    if id_column and feature_column:
        schema = {'header': feature_column, 'sid': id_column}
    elif id_column:
        schema = {'sid': id_column, 'header': ''}
    sess = Session()
    storage_session = sess.storage(storage_engine=engine, options=request_data.get("options"))
    table = storage_session.create_table(address=address, name=name, namespace=namespace,
                                         partitions=request_data.get('partitions', None),
                                         hava_head=request_data.get("head"), schema=schema,
                                         id_delimiter=request_data.get("id_delimiter"), in_serialized=in_serialized,
                                         origin=request_data.get("origin", StorageTableOrigin.TABLE_BIND))
    response = get_json_result(data={"table_name": name, "namespace": namespace})
    if not table.check_address():
        response = get_json_result(retcode=100, retmsg=f'engine {engine} address {address_dict} check failed')
    else:
        DataTableTracker.create_table_tracker(
            table_name=name,
            table_namespace=namespace,
            entity_info={"have_parent": False},
        )
    sess.destroy_all_sessions()
    return response


@manager.route('/download', methods=['get'])
def table_download():
    request_data = request.json
    from fate_flow.component_env_utils.env_utils import import_component_output_depend
    import_component_output_depend()
    data_table_meta = storage.StorageTableMeta(name=request_data.get("name"), namespace=request_data.get("namespace"))
    if not data_table_meta:
        return error_response(response_code=210, retmsg=f'no found table:{request_data.get("namespace")}, {request_data.get("name")}')
    tar_file_name = 'table_{}_{}.tar.gz'.format(request_data.get("namespace"), request_data.get("name"))
    return TableStorage.send_table(
        output_tables_meta={"table": data_table_meta},
        tar_file_name=tar_file_name,
        need_head=request_data.get("head", True)
    )


@manager.route('/delete', methods=['post'])
def table_delete():
    request_data = request.json
    table_name = request_data.get('table_name')
    namespace = request_data.get('namespace')
    data = None
    sess = Session()
    table = sess.get_table(name=table_name, namespace=namespace, ignore_disable=True)
    if table:
        table.destroy()
        data = {'table_name': table_name, 'namespace': namespace}
    sess.destroy_all_sessions()
    if data:
        return get_json_result(data=data)
    return get_json_result(retcode=101, retmsg='no find table')


@manager.route('/disable', methods=['post'])
@manager.route('/enable', methods=['post'])
def table_disable():
    request_data = request.json
    adapter_request_data(request_data)
    disable = True if request.url.endswith("disable") else False
    tables_meta = storage.StorageTableMeta.query_table_meta(filter_fields=dict(**request_data))
    data = []
    if tables_meta:
        for table_meta in tables_meta:
            storage.StorageTableMeta(name=table_meta.f_name,
                                     namespace=table_meta.f_namespace
                                     ).update_metas(disable=disable)
            data.append({'table_name': table_meta.f_name, 'namespace': table_meta.f_namespace})
        return get_json_result(data=data)
    return get_json_result(retcode=101, retmsg='no find table')


@manager.route('/disable/delete', methods=['post'])
def table_delete_disable():
    request_data = request.json
    adapter_request_data(request_data)
    tables_meta = storage.StorageTableMeta.query_table_meta(filter_fields={"disable": True})
    data = []
    sess = Session()
    for table_meta in tables_meta:
        table = sess.get_table(name=table_meta.f_name, namespace=table_meta.f_namespace, ignore_disable=True)
        if table:
            table.destroy()
            data.append({'table_name': table_meta.f_name, 'namespace': table_meta.f_namespace})
    sess.destroy_all_sessions()
    if data:
        return get_json_result(data=data)
    return get_json_result(retcode=101, retmsg='no find table')


@manager.route('/list', methods=['post'])
@validate_request('job_id', 'role', 'party_id')
def get_job_table_list():
    jobs = JobSaver.query_job(**request.json)
    if jobs:
        job = jobs[0]
        tables = get_job_all_table(job)
        return get_json_result(data=tables)
    else:
        return get_json_result(retcode=101, retmsg='no find job')


@manager.route('/<table_func>', methods=['post'])
def table_api(table_func):
    config = request.json
    if table_func == 'table_info':
        table_key_count = 0
        table_partition = None
        table_schema = None
        table_name, namespace = config.get("name") or config.get("table_name"), config.get("namespace")
        table_meta = storage.StorageTableMeta(name=table_name, namespace=namespace)
        address = None
        enable = True
        origin = None
        if table_meta:
            table_key_count = table_meta.get_count()
            table_partition = table_meta.get_partitions()
            table_schema = table_meta.get_schema()
            address = table_meta.get_address().__dict__
            enable = not table_meta.get_disable()
            origin = table_meta.get_origin()
            exist = 1
        else:
            exist = 0
        return get_json_result(data={"table_name": table_name,
                                     "namespace": namespace,
                                     "exist": exist,
                                     "count": table_key_count,
                                     "partition": table_partition,
                                     "schema": table_schema,
                                     "enable": enable,
                                     "origin": origin,
                                     "address": address,
                                     })
    else:
        return get_json_result()


@manager.route('/tracking/source', methods=['post'])
@validate_request("table_name", "namespace")
def table_tracking():
    request_info = request.json
    data = DataTableTracker.get_parent_table(request_info.get("table_name"), request_info.get("namespace"))
    return get_json_result(data=data)


@manager.route('/tracking/job', methods=['post'])
@validate_request("table_name", "namespace")
def table_tracking_job():
    request_info = request.json
    data = DataTableTracker.track_job(request_info.get("table_name"), request_info.get("namespace"), display=True)
    return get_json_result(data=data)


def get_job_all_table(job):
    dsl_parser = schedule_utils.get_job_dsl_parser(dsl=job.f_dsl,
                                                   runtime_conf=job.f_runtime_conf,
                                                   train_runtime_conf=job.f_train_runtime_conf
                                                   )
    _, hierarchical_structure = dsl_parser.get_dsl_hierarchical_structure()
    component_table = {}
    try:
        component_output_tables = Tracker.query_output_data_infos(job_id=job.f_job_id, role=job.f_role,
                                                                  party_id=job.f_party_id)
    except:
        component_output_tables = []
    for component_name_list in hierarchical_structure:
        for component_name in component_name_list:
            component_table[component_name] = {}
            component_input_table = get_component_input_table(dsl_parser, job, component_name)
            component_table[component_name]['input'] = component_input_table
            component_table[component_name]['output'] = {}
            for output_table in component_output_tables:
                if output_table.f_component_name == component_name:
                    component_table[component_name]['output'][output_table.f_data_name] = \
                        {'name': output_table.f_table_name, 'namespace': output_table.f_table_namespace}
    return component_table


def get_component_input_table(dsl_parser, job, component_name):
    component = dsl_parser.get_component_info(component_name=component_name)
    module_name = get_component_module(component_name, job.f_dsl)
    if 'reader' in module_name.lower():
        return job.f_runtime_conf.get("component_parameters", {}).get("role", {}).get(job.f_role, {}).get(str(job.f_roles.get(job.f_role).index(int(job.f_party_id)))).get(component_name)
    task_input_dsl = component.get_input()
    job_args_on_party = TaskExecutor.get_job_args_on_party(dsl_parser=dsl_parser,
                                                           job_runtime_conf=job.f_runtime_conf, role=job.f_role,
                                                           party_id=job.f_party_id)
    config = job_utils.get_job_parameters(job.f_job_id, job.f_role, job.f_party_id)
    task_parameters = RunParameters(**config)
    job_parameters = task_parameters
    component_input_table = TaskExecutor.get_task_run_args(job_id=job.f_job_id, role=job.f_role,
                                                           party_id=job.f_party_id,
                                                           task_id=None,
                                                           task_version=None,
                                                           job_args=job_args_on_party,
                                                           job_parameters=job_parameters,
                                                           task_parameters=task_parameters,
                                                           input_dsl=task_input_dsl,
                                                           get_input_table=True
                                                           )
    return component_input_table


def get_component_module(component_name, job_dsl):
    return job_dsl["components"][component_name]["module"].lower()


def adapter_request_data(request_data):
    if request_data.get("table_name"):
        request_data["name"] = request_data.get("table_name")
