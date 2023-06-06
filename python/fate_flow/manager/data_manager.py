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
import copy
import datetime
import json
import operator
import os
import tarfile
import uuid

from flask import send_file

from fate_arch import storage
from fate_arch.abc import StorageTableABC
from fate_arch.common.base_utils import fate_uuid
from fate_arch.session import Session
from fate_flow.component_env_utils import feature_utils, env_utils
from fate_flow.settings import stat_logger
from fate_flow.db.db_models import DB, TrackingMetric, DataTableTracking
from fate_flow.utils import data_utils
from fate_flow.utils.base_utils import get_fate_flow_directory
from fate_flow.utils.data_utils import get_header_schema, line_extend_uuid


class SchemaMetaParam:
    def __init__(self,
                 delimiter=",",
                 input_format="dense",
                 tag_with_value=False,
                 tag_value_delimiter=":",
                 with_match_id=False,
                 id_list=None,
                 id_range=0,
                 exclusive_data_type=None,
                 data_type="float64",
                 with_label=False,
                 label_name="y",
                 label_type="int"):
        self.input_format = input_format
        self.delimiter = delimiter
        self.tag_with_value = tag_with_value
        self.tag_value_delimiter = tag_value_delimiter
        self.with_match_id = with_match_id
        self.id_list = id_list
        self.id_range = id_range
        self.exclusive_data_type = exclusive_data_type
        self.data_type = data_type
        self.with_label = with_label
        self.label_name = label_name
        self.label_type = label_type
        self.adapter_param()

    def to_dict(self):
        d = {}
        for k, v in self.__dict__.items():
            if v is None:
                continue
            d[k] = v
        return d

    def adapter_param(self):
        if not self.with_label:
            self.label_name = None
            self.label_type = None


class AnonymousGenerator(object):
    @staticmethod
    def update_anonymous_header_with_role(schema, role, party_id):
        obj = env_utils.get_class_object("anonymous_generator")
        return obj.update_anonymous_header_with_role(schema, role, party_id)

    @staticmethod
    def generate_anonymous_header(schema):
        obj = env_utils.get_class_object("anonymous_generator")()
        return obj.generate_anonymous_header(schema)

    @staticmethod
    def migrate_schema_anonymous(anonymous_schema, role, party_id, migrate_mapping):
        obj = env_utils.get_class_object("anonymous_generator")(role, party_id, migrate_mapping)
        return obj.migrate_schema_anonymous(anonymous_schema)

    @staticmethod
    def generate_header(computing_table, schema):
        obj = env_utils.get_class_object("data_format")
        return obj.generate_header(computing_table, schema)

    @staticmethod
    def reconstruct_header(schema):
        obj = env_utils.get_class_object("data_format")
        return obj.reconstruct_header(schema)

    @staticmethod
    def recover_schema(schema):
        obj = env_utils.get_class_object("data_format")
        return obj.recover_schema(schema)


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
    def collect(src_table, part_of_data):
        line_index = 0
        count = 0
        fate_uuid = uuid.uuid1().hex
        for k, v in src_table.collect():
            if src_table.meta.get_extend_sid():
                v = src_table.meta.get_id_delimiter().join([k, v])
                k = line_extend_uuid(fate_uuid, line_index)
                line_index += 1
            yield k, v
            if count <= 100:
                part_of_data.append((k, v))
                count += 1

    @staticmethod
    def read(src_table, schema, part_of_data):
        line_index = 0
        count = 0
        src_table_meta = src_table.meta
        fate_uuid = uuid.uuid1().hex
        if src_table_meta.get_have_head():
            get_head = False
        else:
            get_head = True
        if not src_table.meta.get_extend_sid():
            get_line = data_utils.get_data_line
        elif not src_table_meta.get_auto_increasing_sid():
            get_line = data_utils.get_sid_data_line
        else:
            get_line = data_utils.get_auto_increasing_sid_data_line
        for line in src_table.read():
            if not get_head:
                schema.update(data_utils.get_header_schema(
                    header_line=line,
                    id_delimiter=src_table_meta.get_id_delimiter(),
                    extend_sid=src_table_meta.get_extend_sid(),
                ))
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
            yield k, v
            if count <= 100:
                part_of_data.append((k, v))
                count += 1

    @staticmethod
    def copy_table(src_table: StorageTableABC, dest_table: StorageTableABC):
        part_of_data = []
        src_table_meta = src_table.meta
        schema = {}
        update_schema = False
        if not src_table_meta.get_in_serialized():
            dest_table.put_all(TableStorage.read(src_table, schema, part_of_data))
        else:
            source_header = copy.deepcopy(src_table_meta.get_schema().get("header"))
            TableStorage.update_full_header(src_table_meta)
            dest_table.put_all(TableStorage.collect(src_table, part_of_data))
            schema = src_table.meta.get_schema()
            schema["header"] = source_header
        if schema.get("extend_tag"):
            schema.update({"extend_tag": False})
        _, dest_table.meta = dest_table.meta.update_metas(
            schema=schema if not update_schema else None,
            part_of_data=part_of_data,
            id_delimiter=src_table_meta.get_id_delimiter()
        )
        return dest_table.count()

    @staticmethod
    def update_full_header(table_meta):
        schema = table_meta.get_schema()
        if schema.get("anonymous_header"):
            header = AnonymousGenerator.reconstruct_header(schema)
            schema["header"] = header
            table_meta.set_metas(schema=schema)

    @staticmethod
    def read_table_data(data_table_meta, limit=100):
        if not limit or limit > 100:
            limit = 100
        data_table = storage.StorageTableMeta(
            name=data_table_meta.get_name(),
            namespace=data_table_meta.get_namespace()
        )
        if data_table:
            table_schema = data_table_meta.get_schema()
            out_header = None
            data_list = []
            all_extend_header = {}
            for k, v in data_table_meta.get_part_of_data():
                data_line, is_str, all_extend_header = feature_utils.get_component_output_data_line(
                    src_key=k,
                    src_value=v,
                    schema=table_schema,
                    all_extend_header=all_extend_header
                )
                data_list.append(data_line)
                if len(data_list) == limit:
                    break
            if data_list:
                extend_header = feature_utils.generate_header(all_extend_header, schema=table_schema)
                out_header = get_component_output_data_schema(
                    output_table_meta=data_table_meta,
                    is_str=is_str,
                    extend_header=extend_header
                )

            return {'header': out_header, 'data': data_list}

        return {'header': [], 'data': []}

    @staticmethod
    def send_table(output_tables_meta, tar_file_name="", limit=-1, need_head=True, local_download=False, output_data_file_path=None):
        output_data_file_list = []
        output_data_meta_file_list = []
        output_tmp_dir = os.path.join(get_fate_flow_directory(), 'tmp/{}/{}'.format(datetime.datetime.now().strftime("%Y%m%d"), fate_uuid()))
        for output_name, output_table_meta in output_tables_meta.items():
            output_data_count = 0
            if not local_download:
                output_data_file_path = "{}/{}.csv".format(output_tmp_dir, output_name)
                output_data_meta_file_path = "{}/{}.meta".format(output_tmp_dir, output_name)
            os.makedirs(os.path.dirname(output_data_file_path), exist_ok=True)
            with open(output_data_file_path, 'w') as fw:
                with Session() as sess:
                    output_table = sess.get_table(name=output_table_meta.get_name(),
                                                  namespace=output_table_meta.get_namespace())
                    all_extend_header = {}
                    if output_table:
                        for k, v in output_table.collect():
                            data_line, is_str, all_extend_header = feature_utils.get_component_output_data_line(
                                src_key=k,
                                src_value=v,
                                schema=output_table_meta.get_schema(),
                                all_extend_header=all_extend_header)
                            # save meta
                            if output_data_count == 0:
                                output_data_file_list.append(output_data_file_path)
                                extend_header = feature_utils.generate_header(all_extend_header,
                                                                              schema=output_table_meta.get_schema())
                                header = get_component_output_data_schema(output_table_meta=output_table_meta,
                                                                          is_str=is_str,
                                                                          extend_header=extend_header)
                                if not local_download:
                                    output_data_meta_file_list.append(output_data_meta_file_path)
                                    with open(output_data_meta_file_path, 'w') as f:
                                        json.dump({'header': header}, f, indent=4)
                                if need_head and header and output_table_meta.get_have_head() and \
                                        output_table_meta.get_schema().get("is_display", True):
                                    fw.write('{}\n'.format(','.join(header)))
                            delimiter = output_table_meta.get_id_delimiter() if output_table_meta.get_id_delimiter() else ","
                            fw.write('{}\n'.format(delimiter.join(map(lambda x: str(x), data_line))))
                            output_data_count += 1
                            if output_data_count == limit:
                                break
        if local_download:
            return
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
        return send_file(output_data_tarfile, attachment_filename=tar_file_name, as_attachment=True)


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
                    except Exception as e:
                        stat_logger.warning(e)
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


def get_component_output_data_schema(output_table_meta, extend_header, is_str=False) -> list:
    # get schema
    schema = output_table_meta.get_schema()
    if not schema:
        return []
    header = [schema.get('sid_name') or schema.get('sid', 'sid')]
    if schema.get("extend_tag"):
        header = []
    if "label" in extend_header and schema.get("label_name"):
        extend_header[extend_header.index("label")] = schema.get("label_name")
    header.extend(extend_header)
    if is_str or isinstance(schema.get('header'), str):

        if schema.get("original_index_info"):
            header = [schema.get('sid_name') or schema.get('sid', 'sid')]
            header.extend(AnonymousGenerator.reconstruct_header(schema))
            return header

        if not schema.get('header'):
            if schema.get('sid'):
                return [schema.get('sid')]
            else:
                return []

        if isinstance(schema.get('header'), str):
            schema_header = schema.get('header').split(',')
        elif isinstance(schema.get('header'), list):
            schema_header = schema.get('header')
        else:
            raise ValueError("header type error")
        header.extend([feature for feature in schema_header])

    else:
        header.extend(schema.get('header', []))

    return header
