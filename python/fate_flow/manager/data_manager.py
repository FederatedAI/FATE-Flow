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
import json
import os
import tarfile
from tempfile import TemporaryDirectory

from flask import send_file

from fate_flow.engine.storage import Session


class DataManager:
    @staticmethod
    def send_table(
            output_tables_meta,
            tar_file_name="",
            limit=-1,
            need_head=True,
            local_download=False,
            output_data_file_path=None
    ):
        output_data_file_list = []
        output_data_meta_file_list = []
        with TemporaryDirectory() as output_tmp_dir:
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
                        if output_table:
                            for k, v in output_table.collect():
                                # save meta
                                if output_data_count == 0:
                                    output_data_file_list.append(output_data_file_path)
                                    header = []
                                    for meta_k, meta_v in output_table.get_meta():
                                        header = meta_v.get("header")

                                    if not local_download:
                                        output_data_meta_file_list.append(output_data_meta_file_path)
                                        with open(output_data_meta_file_path, 'w') as f:
                                            json.dump({'header': header}, f, indent=4)
                                    if need_head and header and output_table_meta.get_have_head():
                                        if isinstance(header, list):
                                            header = output_table_meta.get_id_delimiter().join(header)
                                        fw.write(f'{header}\n')
                                delimiter = output_table_meta.get_id_delimiter() if output_table_meta.get_id_delimiter() else ","
                                fw.write('{}\n'.format(delimiter.join([k, v])))
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
            return send_file(output_data_tarfile, attachment_filename=tar_file_name, as_attachment=True)