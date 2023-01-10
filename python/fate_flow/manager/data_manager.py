import datetime
import io
import json
import os
import tarfile

from flask import send_file

from fate_flow.engine.storage import Session
from fate_flow.settings import stat_logger
from fate_flow.utils.file_utils import get_fate_flow_directory


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
                            # save meta
                            if output_data_count == 0:
                                output_data_file_list.append(output_data_file_path)
                                header = output_table_meta.get_id_delimiter.join([
                                    output_table_meta.get_schema().get("sid"),
                                    output_table_meta.get_schema().get("header")]
                                )

                                if not local_download:
                                    output_data_meta_file_list.append(output_data_meta_file_path)
                                    with open(output_data_meta_file_path, 'w') as f:
                                        json.dump({'header': header}, f, indent=4)
                                if need_head and header and output_table_meta.get_have_head():
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