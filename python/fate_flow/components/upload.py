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
import sys
import time
import uuid

from fate_arch import storage, session
from fate_arch.common import EngineType, file_utils, log, path_utils
from fate_arch.common.data_utils import default_input_fs_path
from fate_arch.session import Session
from fate_arch.storage import DEFAULT_ID_DELIMITER, EggRollStoreType, StorageEngine, StorageTableOrigin
from fate_flow.components._base import (
    BaseParam,
    ComponentBase,
    ComponentMeta,
    ComponentInputProtocol,
)
from fate_flow.entity import Metric, MetricMeta
from fate_flow.manager.data_manager import DataTableTracker
from fate_flow.scheduling_apps.client import ControllerClient
from fate_flow.db.job_default_config import JobDefaultConfig
from fate_flow.utils import data_utils, job_utils, process_utils, session_utils, upload_utils
from fate_flow.utils.base_utils import get_fate_flow_directory

LOGGER = log.getLogger()

upload_cpn_meta = ComponentMeta("Upload")


@upload_cpn_meta.bind_param
class UploadParam(BaseParam):
    def __init__(
            self,
            file="",
            head=1,
            id_delimiter=DEFAULT_ID_DELIMITER,
            partition=10,
            namespace="",
            name="",
            storage_engine="",
            storage_address=None,
            destroy=False,
            extend_sid=False,
            auto_increasing_sid=False,
            block_size=1
    ):
        self.file = file
        self.head = head
        self.id_delimiter = id_delimiter
        self.partition = partition
        self.namespace = namespace
        self.name = name
        self.storage_engine = storage_engine
        self.storage_address = storage_address
        self.destroy = destroy
        self.extend_sid = extend_sid
        self.auto_increasing_sid = auto_increasing_sid
        self.block_size = block_size

    def check(self):
        return True


@upload_cpn_meta.bind_runner.on_local
class Upload(ComponentBase):
    def __init__(self):
        super(Upload, self).__init__()
        self.MAX_PARTITIONS = 1024
        self.MAX_BYTES = 1024 * 1024 * 8 * 500
        self.parameters = {}
        self.table = None
        self.is_block = False
        self.session_id = None
        self.session = None
        self.storage_engine = None

    def _run(self, cpn_input: ComponentInputProtocol):
        self.parameters = cpn_input.parameters
        LOGGER.info(self.parameters)
        self.parameters["role"] = cpn_input.roles["role"]
        self.parameters["local"] = cpn_input.roles["local"]
        storage_engine = self.parameters["storage_engine"].upper()
        storage_address = self.parameters["storage_address"]
        # if not set storage, use job storage as default
        if not storage_engine:
            storage_engine = cpn_input.job_parameters.storage_engine
        self.storage_engine = storage_engine
        if not storage_address:
            storage_address = cpn_input.job_parameters.engines_address[
                EngineType.STORAGE
            ]
        job_id = self.task_version_id.split("_")[0]
        if not os.path.isabs(self.parameters.get("file", "")):
            self.parameters["file"] = os.path.join(
                get_fate_flow_directory(), self.parameters["file"]
            )
        if not os.path.exists(self.parameters["file"]):
            raise Exception(
                "%s is not exist, please check the configure"
                % (self.parameters["file"])
            )
        if not os.path.getsize(self.parameters["file"]):
            raise Exception("%s is an empty file" % (self.parameters["file"]))
        name, namespace = self.parameters.get("name"), self.parameters.get("namespace")
        _namespace, _table_name = self.generate_table_name(self.parameters["file"])
        if namespace is None:
            namespace = _namespace
        if name is None:
            name = _table_name
        read_head = self.parameters["head"]
        if read_head == 0:
            head = False
        elif read_head == 1:
            head = True
        else:
            raise Exception("'head' in conf.json should be 0 or 1")
        partitions = self.parameters["partition"]
        if partitions <= 0 or partitions >= self.MAX_PARTITIONS:
            raise Exception(
                "Error number of partition, it should between %d and %d"
                % (0, self.MAX_PARTITIONS)
            )
        self.session_id = job_utils.generate_session_id(
            self.tracker.task_id,
            self.tracker.task_version,
            self.tracker.role,
            self.tracker.party_id,
        )
        sess = Session.get_global()
        self.session = sess
        if self.parameters.get("destroy", False):
            table = sess.get_table(namespace=namespace, name=name)
            if table:
                LOGGER.info(
                    f"destroy table name: {name} namespace: {namespace} engine: {table.engine}"
                )
                try:
                    table.destroy()
                except Exception as e:
                    LOGGER.error(e)
            else:
                LOGGER.info(
                    f"can not found table name: {name} namespace: {namespace}, pass destroy"
                )
        address_dict = storage_address.copy()
        storage_session = sess.storage(
            storage_engine=storage_engine, options=self.parameters.get("options")
        )
        upload_address = {}
        if storage_engine in {StorageEngine.EGGROLL, StorageEngine.STANDALONE}:
            upload_address = {
                "name": name,
                "namespace": namespace,
                "storage_type": EggRollStoreType.ROLLPAIR_LMDB,
            }
        elif storage_engine in {StorageEngine.MYSQL, StorageEngine.HIVE}:
            if not address_dict.get("db") or not address_dict.get("name"):
                upload_address = {"db": namespace, "name": name}
        elif storage_engine in {StorageEngine.PATH}:
            upload_address = {"path": self.parameters["file"]}
        elif storage_engine in {StorageEngine.HDFS}:
            upload_address = {
                "path": default_input_fs_path(
                    name=name,
                    namespace=namespace,
                    prefix=address_dict.get("path_prefix"),
                )
            }
        elif storage_engine in {StorageEngine.LOCALFS}:
            upload_address = {
                "path": default_input_fs_path(
                    name=name,
                    namespace=namespace,
                    storage_engine=storage_engine
                )
            }
        else:
            raise RuntimeError(f"can not support this storage engine: {storage_engine}")
        address_dict.update(upload_address)
        LOGGER.info(f"upload to {storage_engine} storage, address: {address_dict}")
        address = storage.StorageTableMeta.create_address(
            storage_engine=storage_engine, address_dict=address_dict
        )
        self.parameters["partitions"] = partitions
        self.parameters["name"] = name
        self.table = storage_session.create_table(address=address, origin=StorageTableOrigin.UPLOAD, **self.parameters)
        if storage_engine not in [StorageEngine.PATH]:
            data_table_count = self.save_data_table(job_id, name, namespace, storage_engine, head)
        else:
            data_table_count = self.get_data_table_count(
                self.parameters["file"], name, namespace
            )
        self.table.meta.update_metas(in_serialized=True)
        DataTableTracker.create_table_tracker(
            table_name=name,
            table_namespace=namespace,
            entity_info={"job_id": job_id, "have_parent": False},
        )
        LOGGER.info("------------load data finish!-----------------")
        # rm tmp file
        try:
            if "{}/fate_upload_tmp".format(job_id) in self.parameters["file"]:
                LOGGER.info("remove tmp upload file")
                LOGGER.info(os.path.dirname(self.parameters["file"]))
                shutil.rmtree(os.path.dirname(self.parameters["file"]))
        except:
            LOGGER.info("remove tmp file failed")
        LOGGER.info("file: {}".format(self.parameters["file"]))
        LOGGER.info("total data_count: {}".format(data_table_count))
        LOGGER.info("table name: {}, table namespace: {}".format(name, namespace))

    def save_data_table(self, job_id, dst_table_name, dst_table_namespace, storage_engine, head=True):
        input_file = self.parameters["file"]
        input_feature_count = self.get_count(input_file)
        data_head, file_list, table_list = self.split_file(input_file, head, input_feature_count, dst_table_name,
                                                           dst_table_namespace, storage_engine)
        if len(file_list) == 1:
            self.upload_file(input_file, head, job_id, input_feature_count)
        else:
            self.upload_file_block(file_list, data_head, table_list)
        table_count = self.table.count()
        self.table.meta.update_metas(
            count=table_count,
            partitions=self.parameters["partition"],
            extend_sid=self.parameters["extend_sid"],
        )
        self.save_meta(
            dst_table_namespace=dst_table_namespace,
            dst_table_name=dst_table_name,
            table_count=table_count,
        )
        return table_count

    def get_count(self, input_file):
        with open(input_file, "r", encoding="utf-8") as fp:
            count = 0
            for line in fp:
                count += 1
        return count

    def split_file(self, file_path, head, input_feature_count, table_name, namespace, storage_engine):
        data_head = None
        file_list = []
        table_list = []
        block_size = self.parameters.get("block_size", 1)
        if storage_engine not in {StorageEngine.EGGROLL, StorageEngine.STANDALONE} or block_size == 1:
            return data_head, [file_path], None
        if isinstance(block_size, int) and block_size> 1:
            block_line = int(input_feature_count / self.parameters.get("block_size", 5)) + 1
        else:
            raise ValueError(f"block size value error:{block_size}")

        LOGGER.info('start to split file {}'.format(file_path))

        file_dir, name = os.path.split(file_path)
        partno = 0
        name_uuid = uuid.uuid1().hex
        with open(file_path, 'r') as stream:
            if head:
                data_head = stream.readline()
            while True:
                part_file_name = os.path.join(file_dir, name + '_' + str(partno))
                LOGGER.debug('write start %s' % part_file_name)
                part_stream = open(part_file_name, 'w')
                read_count = 0
                while read_count < block_line:
                    read_content = stream.readline()
                    if read_content:
                        part_stream.write(read_content)
                    else:
                        break
                    read_count += 1
                part_stream.close()
                if read_count > 0:
                    file_list.append(part_file_name)
                    table_list.append({"name": table_name + '_' + name_uuid + str(partno), "namespace": namespace})
                if (read_count < block_line):
                    break
                partno += 1
        LOGGER.debug('finish split file {}: {}, {}, {}'.format(file_path, data_head, file_list, table_list))
        return data_head, file_list, table_list

    def upload_file(self, input_file, head, job_id=None, input_feature_count=None, table=None, without_block=True):
        if not table:
            table = self.table
        with open(input_file, "r") as fin:
            lines_count = 0
            if head is True:
                data_head = fin.readline()
                input_feature_count -= 1
                self.update_table_meta(data_head)
            n = 0
            fate_uuid = uuid.uuid1().hex
            get_line = self.get_line()
            while True:
                data = list()
                lines = fin.readlines(JobDefaultConfig.upload_max_bytes)
                line_index = 0
                if lines:
                    # self.append_data_line(lines, data, n)
                    for line in lines:
                        values = line.rstrip().split(self.parameters["id_delimiter"])
                        k, v = get_line(
                            values=values,
                            line_index=line_index,
                            extend_sid=self.parameters["extend_sid"],
                            auto_increasing_sid=self.parameters["auto_increasing_sid"],
                            id_delimiter=self.parameters["id_delimiter"],
                            fate_uuid=fate_uuid,
                        )
                        data.append((k, v))
                        line_index += 1
                    if without_block:
                        lines_count += len(data)
                        save_progress = lines_count / input_feature_count * 100 // 1
                        job_info = {
                            "progress": save_progress,
                            "job_id": job_id,
                            "role": self.parameters["local"]["role"],
                            "party_id": self.parameters["local"]["party_id"],
                        }
                        ControllerClient.update_job(job_info=job_info)
                    table.put_all(data)
                    if n == 0 and without_block:
                        table.meta.update_metas(part_of_data=data)
                else:
                    return
                n += 1

    def upload_file_block(self, file_list, data_head, table_list):
        if data_head:
            self.update_table_meta(data_head)
        upload_process = []
        for block_index, block_file in enumerate(file_list):
            task_dir = os.path.join(job_utils.get_job_directory(job_id=self.tracker.job_id),
                                    self.tracker.role,
                                    str(self.tracker.party_id),
                                    self.tracker.component_name, 'upload')
            os.makedirs(task_dir, exist_ok=True)
            process_cmd = [
                sys.executable or 'python3',
                sys.modules[upload_utils.UploadFile.__module__].__file__,
                '--session_id', self.session_id,
                '--storage', self.storage_engine,
                '--file', block_file,
                '--namespace', table_list[block_index].get("namespace"),
                '--name', table_list[block_index].get("name"),
                '--partitions', self.parameters.get('partition')
            ]
            LOGGER.info(process_cmd)
            job_log_dir = os.path.join(job_utils.get_job_log_directory(job_id=self.tracker.job_id), self.tracker.role,
                                       str(self.tracker.party_id))
            task_log_dir = os.path.join(job_log_dir, self.tracker.component_name, f'block_{block_index}')
            p = process_utils.run_subprocess(job_id=self.tracker.job_id, config_dir=task_dir, process_cmd=process_cmd,
                                             log_dir=task_log_dir)
            upload_process.append(p)
        self.check_upload_process(upload_process)
        self.union_table(table_list)

    def union_table(self, table_list):
        combined_table = self.get_computing_table(self.table.name, self.table.namespace)
        for table_info in table_list:
            table = self.get_computing_table(table_info.get("name"), table_info.get("namespace"))
            combined_table = combined_table.union(table)
            LOGGER.info(combined_table.count())
        session.Session.persistent(computing_table=combined_table,
                                   namespace=self.table.namespace,
                                   name=self.table.name,
                                   schema={},
                                   engine=self.table.engine,
                                   engine_address=self.table.address.__dict__,
                                   token=None)

    def get_computing_table(self, name, namespace, schema=None):
        storage_table_meta = storage.StorageTableMeta(name=name, namespace=namespace)
        computing_table = session.get_computing_session().load(
            storage_table_meta.get_address(),
            schema=schema if schema else storage_table_meta.get_schema(),
            partitions=self.parameters.get("partitions"))
        return computing_table

    def check_upload_process(self, upload_process):
        while True:
            for p in upload_process:
                LOGGER.info(f"pid {p.pid} poll status: {p.poll()}")
                if p.poll() != None:
                    if p.poll() !=0:
                        raise Exception(p.stderr)
                    upload_process.remove(p)
            LOGGER.info(f"running pid:{[p.pid for p in upload_process]}")
            time.sleep(5)
            if not len(upload_process):
                break

    def update_table_meta(self, data_head):
        _, meta = self.table.meta.update_metas(
            schema=data_utils.get_header_schema(
                header_line=data_head,
                id_delimiter=self.parameters["id_delimiter"],
                extend_sid=self.parameters["extend_sid"],
            ),
            auto_increasing_sid=self.parameters["auto_increasing_sid"],
            extend_sid=self.parameters["extend_sid"],
        )
        self.table.meta = meta

    def get_line(self):
        if not self.parameters["extend_sid"]:
            line = data_utils.get_data_line
        elif not self.parameters["auto_increasing_sid"]:
            line = data_utils.get_sid_data_line
        else:
            line = data_utils.get_auto_increasing_sid_data_line
        return line

    def generate_table_name(self, input_file_path):
        str_time = time.strftime("%Y%m%d%H%M%S", time.localtime())
        file_name = input_file_path.split(".")[0]
        file_name = file_name.split("/")[-1]
        return file_name, str_time

    def save_meta(self, dst_table_namespace, dst_table_name, table_count):
        self.tracker.log_output_data_info(
            data_name="upload",
            table_namespace=dst_table_namespace,
            table_name=dst_table_name,
        )
        self.tracker.log_metric_data(
            metric_namespace="upload",
            metric_name="data_access",
            metrics=[Metric("count", table_count)],
        )
        self.tracker.set_metric_meta(
            metric_namespace="upload",
            metric_name="data_access",
            metric_meta=MetricMeta(name="upload", metric_type="UPLOAD"),
        )

    def get_data_table_count(self, path, name, namespace):
        count = path_utils.get_data_table_count(path)
        self.save_meta(
            dst_table_namespace=namespace, dst_table_name=name, table_count=count
        )
        self.table.meta.update_metas(count=count)
        return count
