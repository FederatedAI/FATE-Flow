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
import argparse
import uuid

from fate_arch import storage
from fate_arch.session import Session
from fate_arch.storage import StorageEngine, EggRollStoreType, StorageTableOrigin
from fate_flow.utils import data_utils


class UploadFile(object):
    @classmethod
    def run(cls):
        parser = argparse.ArgumentParser()
        parser.add_argument('--session_id', required=True, type=str, help="session id")
        parser.add_argument('--storage', help="storage engine", type=str)
        parser.add_argument('--file', required=True, type=str, help="file path")
        parser.add_argument('--namespace', required=True, type=str, help="namespace")
        parser.add_argument('--name', required=True, type=str, help="name")
        parser.add_argument('--partitions', required=True, type=int, help="partitions")
        args = parser.parse_args()
        session_id = args.session_id
        with Session(session_id=session_id) as sess:
            storage_session = sess.storage(
                storage_engine=args.storage
            )
            if args.storage in {StorageEngine.EGGROLL, StorageEngine.STANDALONE}:
                upload_address = {
                    "name": args.name,
                    "namespace": args.namespace,
                    "storage_type": EggRollStoreType.ROLLPAIR_LMDB,
                }
            address = storage.StorageTableMeta.create_address(
                storage_engine=args.storage, address_dict=upload_address
            )
            table = storage_session.create_table(address=address, name=args.name, namespace=args.namespace, partitions=args.partitions, origin=StorageTableOrigin.UPLOAD)
            cls.upload(args.file, False, table=table)

    @classmethod
    def upload(cls, input_file, head, table=None, id_delimiter=",", extend_sid=False):
        with open(input_file, "r") as fin:
            if head is True:
                data_head = fin.readline()
                _, meta = table.meta.update_metas(
                    schema=data_utils.get_header_schema(
                        header_line=data_head,
                        id_delimiter=id_delimiter
                    )
                )
                table.meta = meta
            fate_uuid = uuid.uuid1().hex
            get_line = cls.get_line(extend_sid)
            line_index = 0
            n = 0
            while True:
                data = list()
                lines = fin.readlines(1024 * 1024 * 8 * 500)
                if lines:
                    # self.append_data_line(lines, data, n)
                    for line in lines:
                        values = line.rstrip().split(',')
                        k, v = get_line(
                            values=values,
                            line_index=line_index,
                            extend_sid=extend_sid,
                            auto_increasing_sid=False,
                            id_delimiter=id_delimiter,
                            fate_uuid=fate_uuid
                        )
                        data.append((k, v))
                        line_index += 1
                    table.put_all(data)
                    if n == 0:
                        table.meta.update_metas(part_of_data=data[:100])
                    n += 1
                else:
                    return line_index

    @classmethod
    def get_line(self, extend_sid=False):
        if extend_sid:
            line = data_utils.get_sid_data_line
        else:
            line = data_utils.get_data_line
        return line


if __name__ == '__main__':
    UploadFile.run()
