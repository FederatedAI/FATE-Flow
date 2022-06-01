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
import functools
import os
import shutil
import zipfile

from fate_arch.common import file_utils
from fate_flow.utils.log_utils import getLogger
from fate_flow.db.db_models import ComponentProviderInfo
from fate_flow.db.dependence_registry import DependenceRegistry
from fate_flow.entity import ComponentProvider
from fate_flow.entity.types import FateDependenceName, ComponentProviderName, FateDependenceStorageEngine
from fate_flow.settings import FATE_VERSION_DEPENDENCIES_PATH
from fate_flow.worker.base_worker import BaseWorker
from fate_flow.utils.base_utils import get_fate_flow_python_directory

LOGGER = getLogger()


def upload_except_exit(func):
    @functools.wraps(func)
    def _wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            provider = kwargs.get("provider")
            dependence_type = kwargs.get("dependence_type")
            storage_engine = FateDependenceStorageEngine.HDFS.value
            storage_meta = {
                "f_storage_engine": storage_engine,
                "f_type": dependence_type,
                "f_version": provider.version,
                "f_upload_status": False
            }
            DependenceRegistry.save_dependencies_storage_meta(storage_meta)
            raise e
    return _wrapper


class DependenceUpload(BaseWorker):
    def _run(self):
        provider = ComponentProvider(**self.args.config.get("provider"))
        dependence_type = self.args.dependence_type
        self.upload_dependencies_to_hadoop(provider=provider, dependence_type=dependence_type)

    @classmethod
    @upload_except_exit
    def upload_dependencies_to_hadoop(cls, provider, dependence_type, storage_engine=FateDependenceStorageEngine.HDFS.value):
        LOGGER.info(f'upload {dependence_type} dependencies to hadoop')
        LOGGER.info(f'dependencies loading ...')
        if dependence_type == FateDependenceName.Python_Env.value:
            # todo: version python env
            target_file = os.path.join(FATE_VERSION_DEPENDENCIES_PATH, provider.version, "python_env.zip")
            source_path = os.path.dirname(os.path.dirname(os.getenv("VIRTUAL_ENV")))
            cls.rewrite_pyvenv_cfg(os.path.join(os.getenv("VIRTUAL_ENV"), "pyvenv.cfg"), "python_env")
            env_dir_list = ["python", "miniconda3"]
            cls.zip_dir(source_path, target_file, env_dir_list)

            dependencies_conf = {"executor_python": f"./{dependence_type}/python/venv/bin/python",
                                 "driver_python": f"{os.path.join(os.getenv('VIRTUAL_ENV'), 'bin', 'python')}"}
        else:
            fate_code_dependencies = {
                "fate_flow": get_fate_flow_python_directory("fate_flow"),
                "fate_arch": file_utils.get_fate_python_directory("fate_arch"),
                "conf": file_utils.get_project_base_directory("conf")
            }
            fate_flow_snapshot_time = DependenceRegistry.get_modify_time(fate_code_dependencies["fate_flow"])
            fate_code_base_dir = os.path.join(FATE_VERSION_DEPENDENCIES_PATH, provider.version, "fate_code", "fate")
            python_base_dir = os.path.join(fate_code_base_dir, "python")
            if os.path.exists(os.path.dirname(python_base_dir)):
                shutil.rmtree(os.path.dirname(python_base_dir))
            for key, path in fate_code_dependencies.items():
                cls.copy_dir(path, os.path.join(python_base_dir, key))
                if key == "conf":
                    cls.move_dir(os.path.join(python_base_dir, key), os.path.dirname(fate_code_base_dir))
            if provider.name == ComponentProviderName.FATE.value:
                source_path = provider.path
            else:
                source_path = ComponentProviderInfo.get_or_none(
                    ComponentProviderInfo.f_version == provider.version,
                    ComponentProviderInfo.f_provider_name == ComponentProviderName.FATE.value
                ).f_path
            cls.copy_dir(source_path, os.path.join(python_base_dir, "federatedml"))
            target_file = os.path.join(FATE_VERSION_DEPENDENCIES_PATH, provider.version, "fate.zip")
            cls.zip_dir(os.path.dirname(fate_code_base_dir), target_file)
            dependencies_conf = {"executor_env_pythonpath": f"./{dependence_type}/fate/python:$PYTHONPATH"}
        LOGGER.info(f'dependencies loading success')

        LOGGER.info(f'start upload')
        snapshot_time = DependenceRegistry.get_modify_time(source_path)
        storage_dir = f"/fate_dependence/{provider.version}"
        os.system(f" {os.getenv('HADOOP_HOME')}/bin/hdfs dfs -mkdir -p  {storage_dir}")
        status = os.system(f"{os.getenv('HADOOP_HOME')}/bin/hdfs dfs -put -f {target_file} {storage_dir}")
        LOGGER.info(f'upload end, status is {status}')
        if status == 0:
            storage_path = os.path.join(storage_dir, os.path.basename(target_file))
            storage_meta = {
                "f_storage_engine": storage_engine,
                "f_type": dependence_type,
                "f_version": provider.version,
                "f_storage_path": storage_path,
                "f_snapshot_time": snapshot_time,
                "f_fate_flow_snapshot_time": fate_flow_snapshot_time if dependence_type == FateDependenceName.Fate_Source_Code.value else None,
                "f_dependencies_conf": {"archives": "#".join([storage_path, dependence_type])},
                "f_upload_status": False,
                "f_pid": 0
            }
            storage_meta["f_dependencies_conf"].update(dependencies_conf)
            DependenceRegistry.save_dependencies_storage_meta(storage_meta)
        else:
            raise Exception(f"{os.getenv('HADOOP_HOME')}/bin/hdfs dfs -put {target_file} {storage_dir} failed status: {status}")
        return storage_meta

    @classmethod
    def zip_dir(cls, input_dir_path, output_zip_full_name, dir_list=None):
        with zipfile.ZipFile(output_zip_full_name, "w", zipfile.ZIP_DEFLATED) as zip_object:
            if not dir_list:
                cls.zip_write(zip_object, input_dir_path, input_dir_path)
            else:
                for dir_name in dir_list:
                    dir_path = os.path.join(input_dir_path, dir_name)
                    cls.zip_write(zip_object, dir_path, input_dir_path)

    @classmethod
    def zip_write(cls, zip_object, dir_path, input_dir_path):
        for path, dirnames, filenames in os.walk(dir_path):
            fpath = path.replace(input_dir_path, '')
            for filename in filenames:
                zip_object.write(os.path.join(path, filename), os.path.join(fpath, filename))

    @staticmethod
    def copy_dir(source_path, target_path):
        if os.path.exists(target_path):
            shutil.rmtree(target_path)
        shutil.copytree(source_path, target_path)

    @staticmethod
    def move_dir(source_path, target_path):
        shutil.move(source_path, target_path)


    @classmethod
    def rewrite_pyvenv_cfg(cls, file, dir_name):
        import re
        bak_file = file + '.bak'
        shutil.copyfile(file, bak_file)
        with open(file, "w") as fw:
            with open(bak_file, 'r') as fr:
                lines = fr.readlines()
                match_str = None
                for line in lines:
                    change_line = re.findall(".*=(.*)miniconda.*", line)
                    if change_line:
                        if not match_str:
                            match_str = change_line[0]
                        line = re.sub(match_str, f" ./{dir_name}/", line)
                    fw.write(line)


if __name__ == '__main__':
    DependenceUpload().run()
