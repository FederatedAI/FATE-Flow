import os
import shutil
import zipfile

from fate_arch.common import file_utils, EngineType
from fate_arch.common.log import schedule_logger
from fate_flow.db.db_models import DependenciesStorageMeta, ComponentVersionInfo, DB
from fate_flow.entity.component_provider import ComponentProvider
from fate_flow.entity.types import FateDependenceName, ComponentProviderName
from fate_flow.manager.resource_manager import ResourceManager
from fate_flow.settings import FATE_VERSION_DEPENDENCIES_PATH


class DependenceManager:
    def __init__(self, provider_info, job_id, only_check=False, storage_engine="HDFS"):
        self.dependence_config = None
        self.job_id = job_id
        self.storage_engine = storage_engine
        self.provider = ComponentProvider(**provider_info)
        self.check_dependence(only_check)

    def check_dependence(self, only_check):
        schedule_logger(self.job_id).info("start check dependence")
        dependence_config = {}
        for dependence_type in [FateDependenceName.Fate_Source_Code, FateDependenceName.Python_Env]:
            dependencies_storage_info = self.get_dependencies_storage_meta(storage_engine=self.storage_engine,
                                                                           version=self.provider.version,
                                                                           dependence_type=dependence_type,
                                                                           get_or_one=True
                                                                           )
            upload = False
            schedule_logger(self.job_id).info(f"{dependence_type} dependencies storage info: {dependencies_storage_info}")
            if dependencies_storage_info:
                dependencies_storage_info = dependencies_storage_info.to_dict()
                if dependence_type == FateDependenceName.Fate_Source_Code and self.provider.name == ComponentProviderName.FATE_ALGORITHM:
                    if self.get_modify_time(self.provider.path) != dependencies_storage_info.get("f_snapshot_time"):
                        upload = True
            else:
                upload =True
            schedule_logger(self.job_id).info(f"upload {dependence_type} dependence status:{upload}")
            if upload:
                if only_check:
                    raise Exception(f"no found {dependence_type} dependence")
                schedule_logger(self.job_id).info(f"start upload {dependence_type} dependence, storage engine {self.storage_engine}")
                dependencies_storage_info = self.upload_dependencies_to_hadoop(self.provider, dependence_type, self.storage_engine)
                schedule_logger(self.job_id).info(f"upload {dependence_type} dependence success")
                schedule_logger(self.job_id).info(f"dependence storage info: {dependencies_storage_info}")
            dependence_config[dependence_type] = dependencies_storage_info
        schedule_logger(self.job_id).info(f"check dependence success, dependence config: {dependence_config}")
        self.dependence_config = dependence_config

    def get_executor_env_pythonpath(self):
        return self.dependence_config.get(FateDependenceName.Fate_Source_Code).get("f_dependencies_conf").get(
            "executor_env_pythonpath")

    def get_executor_python_env(self):
        return self.dependence_config.get(FateDependenceName.Python_Env).get("f_dependencies_conf").get(
            "executor_python")

    def get_driver_python_env(self):
        return self.dependence_config.get(FateDependenceName.Python_Env).get("f_dependencies_conf").get(
            "driver_python")

    def get_archives(self):
        archives = []
        name_node = ResourceManager.get_engine_registration_info(engine_type=EngineType.STORAGE,
                                                                 engine_name=self.storage_engine
                                                                 ).f_engine_config.get("name_node")
        schedule_logger(self.job_id).info(f"name node: {name_node}")
        for dependence_type in [FateDependenceName.Fate_Source_Code, FateDependenceName.Python_Env]:
            archives.append(
                name_node + self.dependence_config.get(dependence_type).get("f_dependencies_conf").get("archives")
            )
        return ','.join(archives)

    @classmethod
    def upload_dependencies_to_hadoop(cls, provider, dependence_type, storage_engine):
        if dependence_type == FateDependenceName.Python_Env:
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
                "fate_flow": file_utils.get_python_base_directory("fate_flow"),
                "fate_arch": file_utils.get_python_base_directory("fate_arch"),
                "conf": file_utils.get_project_base_directory("conf")
            }
            fate_code_base_dir = os.path.join(FATE_VERSION_DEPENDENCIES_PATH, provider.version, "fate_code", "python")
            if not os.path.exists(fate_code_base_dir):
                for key, path in fate_code_dependencies.items():
                    cls.copy_dir(path, os.path.join(fate_code_base_dir, key))
                    if key == "conf":
                        cls.move_dir(os.path.join(fate_code_base_dir, key), os.path.dirname(fate_code_base_dir))
            if provider.name == ComponentProviderName.FATE_ALGORITHM:
                source_path = provider.path
            else:
                source_path = ComponentVersionInfo.get_or_none(
                    ComponentVersionInfo.f_version == provider.version,
                    ComponentVersionInfo.f_provider_name == ComponentProviderName.FATE_ALGORITHM
                ).f_path
            cls.copy_dir(source_path, os.path.join(fate_code_base_dir, "federatedml"))
            target_file = os.path.join(FATE_VERSION_DEPENDENCIES_PATH, provider.version, "python.zip")
            cls.zip_dir(os.path.dirname(fate_code_base_dir), target_file)
            dependencies_conf = {"executor_env_pythonpath": f"./{dependence_type}/python:$PYTHONPATH"}
        snapshot_time = cls.get_modify_time(source_path)
        storage_dir = f"/fate_dependence/{provider.version}"
        os.system(f"hdfs dfs -mkdir -p  {storage_dir}")
        status = os.system(f"hdfs dfs -put -f {target_file} {storage_dir}")
        if status == 0:
            storage_path = os.path.join(storage_dir, os.path.basename(target_file))
            storage_meta = {
                "f_storage_engine": storage_engine,
                "f_type": dependence_type,
                "f_version": provider.version,
                "f_storage_path": storage_path,
                "f_snapshot_time": snapshot_time,
                "f_dependencies_conf": {"archives": "#".join([storage_path, dependence_type])}
            }
            storage_meta["f_dependencies_conf"].update(dependencies_conf)
            cls.save_dependencies_storage_meta(storage_meta)
        else:
            raise Exception(f"hdfs dfs -put {target_file} {storage_dir} failed status: {status}")
        return storage_meta

    @classmethod
    @DB.connection_context()
    def get_dependencies_storage_meta(cls, storage_engine, version, dependence_type, get_or_one=False):
        dependencies_storage_info = DependenciesStorageMeta.select().where(
            DependenciesStorageMeta.f_storage_engine == storage_engine,
            DependenciesStorageMeta.f_version == version,
            DependenciesStorageMeta.f_type == dependence_type)
        if get_or_one:
            return dependencies_storage_info[0] if dependencies_storage_info else None
        return dependencies_storage_info

    @classmethod
    @DB.connection_context()
    def save_dependencies_storage_meta(cls, storage_meta):
        entity_model, status = DependenciesStorageMeta.get_or_create(
            f_storage_engine=storage_meta.get("f_storage_engine"),
            f_type=storage_meta.get("f_type"),
            f_version=storage_meta.get("f_version"),
            defaults=storage_meta)
        if status is False:
            for key in storage_meta:
                setattr(entity_model, key, storage_meta[key])
            entity_model.save(force_insert=False)



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
    def get_modify_time(cls, path):
        return int(os.path.getmtime(path)*1000)

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
