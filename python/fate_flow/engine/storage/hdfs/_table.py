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
import io
from typing import Iterable

from pyarrow import fs

from fate_flow.engine.storage import StorageTableBase
from fate_flow.engine.storage._types import StorageEngine
from fate_flow.manager.data.data_manager import DataManager
from fate_flow.utils.log import getLogger


LOGGER = getLogger()


class StorageTable(StorageTableBase):
    def __init__(
            self,
            address=None,
            name: str = None,
            namespace: str = None,
            partitions: int = 1,
            options=None,
    ):
        super(StorageTable, self).__init__(
            name=name,
            namespace=namespace,
            address=address,
            partitions=partitions,
            options=options,
            engine=StorageEngine.HDFS
        )
        try:
            from pyarrow import HadoopFileSystem
            HadoopFileSystem(self.path)
        except Exception as e:
            LOGGER.warning(f"load libhdfs failed: {e}")

        self._hdfs_client = fs.HadoopFileSystem.from_uri(self.path)

    def check_address(self):
        return self._exist()

    def _put_all(
            self, kv_list: Iterable, append=True, assume_file_exist=False, **kwargs
    ):

        client = self._hdfs_client
        path = self.file_path
        LOGGER.info(f"put in hdfs file: {path}")
        if append and (assume_file_exist or self._exist(path)):
            stream = client.open_append_stream(
                path=path, compression=None
            )
        else:
            stream = client.open_output_stream(
                path=path, compression=None
            )

        counter = self._meta.get_count() if self._meta.get_count() else 0
        with io.TextIOWrapper(stream) as writer:
            for k, v in kv_list:
                writer.write(DataManager.serialize_data(k, v))
                writer.write("\n")
                counter = counter + 1
        self._meta.update_metas(count=counter)

    def _collect(self, **kwargs) -> list:
        for line in self._as_generator():
            yield DataManager.deserialize_data(line.rstrip())

    def _read(self) -> list:
        for line in self._as_generator():
            yield line

    def _destroy(self):
        self._hdfs_client.delete_file(self.file_path)

    def _count(self):
        count = 0
        if self._meta.get_count():
            return self._meta.get_count()
        for _ in self._as_generator():
            count += 1
        return count

    def close(self):
        pass

    @property
    def path(self) -> str:
        return f"{self._address.name_node}/{self._address.path}"

    @property
    def file_path(self) -> str:
        return f"{self._address.path}"

    def _exist(self, path=None):
        if not path:
            path = self.file_path
        info = self._hdfs_client.get_file_info([path])[0]
        return info.type != fs.FileType.NotFound

    def _as_generator(self):
        file = self.file_path
        LOGGER.info(f"as generator: {file}")
        info = self._hdfs_client.get_file_info([file])[0]
        if info.type == fs.FileType.NotFound:
            raise FileNotFoundError(f"file {file} not found")

        elif info.type == fs.FileType.File:
            with io.TextIOWrapper(
                buffer=self._hdfs_client.open_input_stream(self.path), encoding="utf-8"
            ) as reader:
                for line in reader:
                    yield line
        else:
            selector = fs.FileSelector(file)
            file_infos = self._hdfs_client.get_file_info(selector)
            for file_info in file_infos:
                if file_info.base_name == "_SUCCESS":
                    continue
                assert (
                    file_info.is_file
                ), f"{self.path} is directory contains a subdirectory: {file_info.path}"
                with io.TextIOWrapper(
                        buffer=self._hdfs_client.open_input_stream(file_info.path),
                        encoding="utf-8",
                ) as reader:
                    for line in reader:
                        yield line
