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
import datetime
import io
import json
import operator
import os
import shutil
import tarfile
import uuid

from flask import send_file

from fate_arch.abc import StorageTableABC
from fate_arch.common.base_utils import fate_uuid
from fate_arch.session import Session
from fate_flow.component_env_utils import feature_utils
from fate_flow.settings import stat_logger
from fate_flow.db.db_models import DB, TrackingMetric, DataTableTracking
from fate_flow.utils import data_utils
from fate_flow.utils.base_utils import get_fate_flow_directory
from fate_flow.utils.data_utils import get_header_schema


class DataTableTracker(object):
    @classmethod
    @DB.connection_context()
    def create_table_tracker(cls, table_name, table_namespace, entity_info):
        tracker = DataTableTracking()
        tracker.f_table_name = table_name
        tracker.f_table_namespace = table_namespace
        for k, v in entity_info.items():
            attr_name = 'f_%s' % k
            if hasattr(DataTableTracking, attr_name):
                setattr(tracker, attr_name, v)
        if entity_info.get("have_parent"):
            parent_trackers = DataTableTracking.select().where(
                DataTableTracking.f_table_name == entity_info.get("parent_table_name"),
                DataTableTracking.f_table_namespace == entity_info.get("parent_table_namespace")).order_by(DataTableTracking.f_create_time.desc())
            if not parent_trackers:
                tracker.f_source_table_name = entity_info.get("parent_table_name")
                tracker.f_source_table_namespace = entity_info.get("parent_table_namespace")
            else:
                parent_tracker = parent_trackers[0]
                if parent_tracker.f_have_parent:
                    tracker.f_source_table_name = parent_tracker.f_source_table_name
                    tracker.f_source_table_namespace = parent_tracker.f_source_table_namespace
                else:
                    tracker.f_source_table_name = parent_tracker.f_table_name
                    tracker.f_source_table_namespace = parent_tracker.f_table_namespace
        rows = tracker.save(force_insert=True)
        if rows != 1:
            raise Exception("Create {} failed".format(tracker))
        return tracker

    @classmethod
    @DB.connection_context()
    def query_tracker(cls, table_name, table_namespace, is_parent=False):
        if not is_parent:
            filters = [operator.attrgetter('f_table_name')(DataTableTracking) == table_name,
                       operator.attrgetter('f_table_namespace')(DataTableTracking) == table_namespace]
        else:
            filters = [operator.attrgetter('f_parent_table_name')(DataTableTracking) == table_name,
                       operator.attrgetter('f_parent_table_namespace')(DataTableTracking) == table_namespace]
        trackers = DataTableTracking.select().where(*filters)
        return [tracker for tracker in trackers]


    @classmethod
    @DB.connection_context()
    def get_parent_table(cls, table_name, table_namespace):
        trackers = DataTableTracker.query_tracker(table_name, table_namespace)
        if not trackers:
            raise Exception(f"no found table: table name {table_name}, table namespace {table_namespace}")
        else:
            parent_table_info = []
            for tracker in trackers:
                if not tracker.f_have_parent:
                    return []
                else:
                    parent_table_info.append({"parent_table_name": tracker.f_parent_table_name,
                                              "parent_table_namespace": tracker.f_parent_table_namespace,
                                              "source_table_name": tracker.f_source_table_name,
                                              "source_table_namespace": tracker.f_source_table_namespace
                                              })
        return parent_table_info

    @classmethod
    @DB.connection_context()
    def track_job(cls, table_name, table_namespace, display=False):
        trackers = DataTableTracker.query_tracker(table_name, table_namespace, is_parent=True)
        job_id_list = []
        for tracker in trackers:
            job_id_list.append(tracker.f_job_id)
        job_id_list = list(set(job_id_list))
        return {"count": len(job_id_list)} if not display else {"count": len(job_id_list), "job": job_id_list}


class TableStorage:
    @staticmethod
    def copy_table(src_table: StorageTableABC, dest_table: StorageTableABC, deserialize_value=False):
        count = 0
        data_temp = []
        part_of_data = []
        src_table_meta = src_table.meta
        schema = {}
        update_schema = False
        if not src_table_meta.get_in_serialized():
            if src_table_meta.get_have_head():
                get_head = False
            else:
                get_head = True
            line_index = 0
            fate_uuid = uuid.uuid1().hex
            if not src_table.meta.get_extend_sid():
                get_line = data_utils.get_data_line
            elif not src_table_meta.get_auto_increasing_sid():
                get_line = data_utils.get_sid_data_line
            else:
                get_line = data_utils.get_auto_increasing_sid_data_line
            for line in src_table.read():
                if not get_head:
                    schema = data_utils.get_header_schema(
                        header_line=line,
                        id_delimiter=src_table_meta.get_id_delimiter(),
                        extend_sid=src_table_meta.get_extend_sid(),
                    )
                    get_head = True
                    continue
                values = line.rstrip().split(src_table.meta.get_id_delimiter())
                k, v = get_line(
                    values=values,
                    line_index=line_index,
                    extend_sid=src_table.meta.get_extend_sid(),
                    auto_increasing_sid=src_table.meta.get_auto_increasing_sid(),
                    id_delimiter=src_table.meta.get_id_delimiter(),
                    fate_uuid=fate_uuid,
                )
                line_index += 1
                count = TableStorage.put_in_table(
                    table=dest_table,
                    k=k,
                    v=v,
                    temp=data_temp,
                    count=count,
                    part_of_data=part_of_data,
                )
        else:
            for k, v in src_table.collect():
                if deserialize_value:
                    # writer component: deserialize value
                    v, extend_header = feature_utils.get_deserialize_value(v, dest_table.meta.get_id_delimiter())
                    if not update_schema:
                        header_list = get_component_output_data_schema(src_table.meta, extend_header)
                        schema = get_header_schema(dest_table.meta.get_id_delimiter().join(header_list),
                                                   dest_table.meta.get_id_delimiter())
                        _, dest_table.meta = dest_table.meta.update_metas(schema=schema)
                        update_schema = True
                count = TableStorage.put_in_table(
                    table=dest_table,
                    k=k,
                    v=v,
                    temp=data_temp,
                    count=count,
                    part_of_data=part_of_data,
                )
            schema = src_table.meta.get_schema()
        if data_temp:
            dest_table.put_all(data_temp)
        dest_table.meta.update_metas(schema=schema if not update_schema else None, part_of_data=part_of_data)
        return dest_table.count()

    @staticmethod
    def put_in_table(table: StorageTableABC, k, v, temp, count, part_of_data, max_num=10000):
        temp.append((k, v))
        if count < 100:
            part_of_data.append((k, v))
        if len(temp) == max_num:
            table.put_all(temp)
            temp.clear()
        return count + 1

    @staticmethod
    def send_table(output_tables_meta, tar_file_name, limit=-1, need_head=True):
        output_data_file_list = []
        output_data_meta_file_list = []
        output_tmp_dir = os.path.join(get_fate_flow_directory(), 'tmp/{}/{}'.format(datetime.datetime.now().strftime("%Y%m%d"), fate_uuid()))
        for output_name, output_table_meta in output_tables_meta.items():
            output_data_count = 0
            output_data_file_path = "{}/{}.csv".format(output_tmp_dir, output_name)
            output_data_meta_file_path = "{}/{}.meta".format(output_tmp_dir, output_name)
            os.makedirs(os.path.dirname(output_data_file_path), exist_ok=True)
            with open(output_data_file_path, 'w') as fw:
                with Session() as sess:
                    output_table = sess.get_table(name=output_table_meta.get_name(),
                                                  namespace=output_table_meta.get_namespace())
                    if output_table:
                        for k, v in output_table.collect():
                            data_line, is_str, extend_header = feature_utils.get_component_output_data_line(src_key=k,
                                                                                                            src_value=v,
                                                                                                            schema=output_table_meta.get_schema())
                            # save meta
                            if output_data_count == 0:
                                output_data_file_list.append(output_data_file_path)
                                header = get_component_output_data_schema(output_table_meta=output_table_meta,
                                                                          is_str=is_str,
                                                                          extend_header=extend_header)
                                output_data_meta_file_list.append(output_data_meta_file_path)
                                with open(output_data_meta_file_path, 'w') as f:
                                    json.dump({'header': header}, f, indent=4)
                                if need_head and header and output_table_meta.get_have_head():
                                    fw.write('{}\n'.format(','.join(header)))
                            fw.write('{}\n'.format(','.join(map(lambda x: str(x), data_line))))
                            output_data_count += 1
                            if output_data_count == limit:
                                break
            # tar
        output_data_tarfile = "{}/{}".format(output_tmp_dir, tar_file_name)
        tar = tarfile.open(output_data_tarfile, mode='w:gz')
        for index in range(0, len(output_data_file_list)):
            tar.add(output_data_file_list[index], os.path.relpath(output_data_file_list[index], output_tmp_dir))
            tar.add(output_data_meta_file_list[index],
                    os.path.relpath(output_data_meta_file_list[index], output_tmp_dir))
        tar.close()
        for key, path in enumerate(output_data_file_list):
            try:
                os.remove(path)
                os.remove(output_data_meta_file_list[key])
            except Exception as e:
                # warning
                stat_logger.warning(e)
        return send_file(output_data_tarfile, attachment_filename=tar_file_name)


def delete_tables_by_table_infos(output_data_table_infos):
    data = []
    status = False
    with Session() as sess:
        for output_data_table_info in output_data_table_infos:
            table_name = output_data_table_info.f_table_name
            namespace = output_data_table_info.f_table_namespace
            table_info = {'table_name': table_name, 'namespace': namespace}
            if table_name and namespace and table_info not in data:
                table = sess.get_table(table_name, namespace)
                if table:
                    try:
                        table.destroy()
                        data.append(table_info)
                        status = True
                    except:
                        pass
    return status, data


def delete_metric_data(metric_info):
    status = delete_metric_data_from_db(metric_info)
    return f"delete status: {status}"


@DB.connection_context()
def delete_metric_data_from_db(metric_info):
    tracking_metric_model = type(TrackingMetric.model(table_index=metric_info.get("job_id")[:8]))
    operate = tracking_metric_model.delete().where(*get_delete_filters(tracking_metric_model, metric_info))
    return operate.execute() > 0


def get_delete_filters(tracking_metric_model, metric_info):
    delete_filters = []
    primary_keys = ["job_id", "role", "party_id", "component_name"]
    for key in primary_keys:
        if key in metric_info:
            delete_filters.append(operator.attrgetter("f_%s" % key)(tracking_metric_model) == metric_info[key])
    return delete_filters


def get_component_output_data_schema(output_table_meta, extend_header, is_str=False):
    # get schema
    schema = output_table_meta.get_schema()
    if not schema:
        return []
    header = [schema.get('sid_name', 'sid')]
    if "label" in extend_header and schema.get("label_name"):
        extend_header[extend_header.index("label")] = schema.get("label_name")
    header.extend(extend_header)
    if is_str or isinstance(schema.get('header'), str):
        if not schema.get('header'):
            if schema.get('sid'):
                return [schema.get('sid')]
            else:
                return None
        header.extend([feature for feature in schema.get('header').split(',')])
    else:
        header.extend(schema.get('header', []))
    return header
