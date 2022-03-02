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

from fate_flow.utils.log_utils import schedule_logger
from fate_arch import session, storage
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
    def upload(cls, input_file, head, job_id=None, input_feature_count=None, table=None, without_block=True):
        with open(input_file, "r") as fin:
            lines_count = 0
            n = 0
            fate_uuid = uuid.uuid1().hex
            get_line = cls.get_line()
            while True:
                data = list()
                lines = fin.readlines(1024 * 1024 * 8 * 500)
                line_index = 0
                if lines:
                    # self.append_data_line(lines, data, n)
                    for line in lines:
                        values = line.rstrip().split(',')
                        k, v = get_line(
                            values=values,
                            line_index=line_index,
                            extend_sid=False,
                            auto_increasing_sid=False,
                            id_delimiter=',',
                            fate_uuid=fate_uuid,
                        )
                        data.append((k, v))
                        line_index += 1
                    table.put_all(data)
                else:
                    return
                n += 1

    @classmethod
    def get_line(cls):
        line = data_utils.get_data_line
        return line



if __name__ == '__main__':
    UploadFile.run()
