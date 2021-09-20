from fate_arch.common import EngineType
from fate_arch.common.log import schedule_logger
from fate_arch.computing import ComputingEngine
from fate_flow.db.dependence_registry import DependenceRegistry
from fate_flow.entity import ComponentProvider
from fate_flow.entity.types import FateDependenceName, ComponentProviderName, FateDependenceStorageEngine, WorkerName
from fate_flow.manager.provider_manager import ProviderManager
from fate_flow.manager.resource_manager import ResourceManager
from fate_flow.manager.worker_manager import WorkerManager
from fate_flow.settings import DEPENDENT_DISTRIBUTION
from fate_flow.utils import schedule_utils
from fate_flow.utils.config_adapter import JobRuntimeConfigAdapter


class DependenceManager:
    dependence_config = None

    @classmethod
    def init(cls, provider):
        cls.set_version_dependence(provider)

    @classmethod
    def set_version_dependence(cls, provider, storage_engine=FateDependenceStorageEngine.HDFS.value):
        dependence_config = {}
        for dependence_type in [FateDependenceName.Fate_Source_Code.value, FateDependenceName.Python_Env.value]:
            dependencies_storage_info = DependenceRegistry.get_dependencies_storage_meta(storage_engine=storage_engine,
                                                                                         version=provider.version,
                                                                                         type=dependence_type,
                                                                                         get_or_one=True
                                                                                         )
            dependence_config[dependence_type] = dependencies_storage_info.to_dict()
        cls.dependence_config = dependence_config

    @classmethod
    def check_upload(cls, job_id, provider_group, storage_engine=FateDependenceStorageEngine.HDFS.value):
        schedule_logger(job_id).info("start Check if need to upload dependencies")
        schedule_logger(job_id).info(f"{provider_group}")
        upload_details = {}
        check_tag = True
        upload_total = 0
        for version, provider_info in provider_group.items():
            upload_details[version] = {}
            provider = ComponentProvider(**provider_info)
            for dependence_type in [FateDependenceName.Fate_Source_Code.value, FateDependenceName.Python_Env.value]:
                schedule_logger(job_id).info(f"{dependence_type}")
                dependencies_storage_info = DependenceRegistry.get_dependencies_storage_meta(
                    storage_engine=storage_engine,
                    version=provider.version,
                    type=dependence_type,
                    get_or_one=True
                    )
                need_upload = False
                if dependencies_storage_info:
                    if dependencies_storage_info.f_upload_status:
                        # version dependence uploading
                        check_tag = False
                        continue
                    elif not dependencies_storage_info.f_storage_path:
                        need_upload = True
                        upload_total += 1

                    elif dependence_type == FateDependenceName.Fate_Source_Code.value and provider.name == ComponentProviderName.FATE_ALGORITHM.value:
                        if DependenceRegistry.get_modify_time(provider.path) !=\
                                dependencies_storage_info.f_snapshot_time:
                            need_upload = True
                            upload_total += 1
                else:
                    need_upload = True
                    upload_total += 1
                if need_upload:
                    upload_details[version][dependence_type] = provider
        if upload_total > 0:
            check_tag = False
        schedule_logger(job_id).info(f"Check dependencies result: {check_tag}, {upload_details}")
        return check_tag, upload_total > 0, upload_details

    @classmethod
    def check_job_dependence(cls, job):
        if not DEPENDENT_DISTRIBUTION:
            return True
        engine_name = JobRuntimeConfigAdapter(job.f_runtime_conf).get_job_computing_engine()
        schedule_logger(job.f_job_id).info(f"job engine name: {engine_name}")
        if engine_name not in [ComputingEngine.SPARK]:
            return True
        dsl_parser = schedule_utils.get_job_dsl_parser(dsl=job.f_dsl, runtime_conf=job.f_runtime_conf,
                                                       train_runtime_conf=job.f_train_runtime_conf)
        provider_group = ProviderManager.get_job_provider_group(dsl_parser=dsl_parser)
        version_provider_info = {}
        fate_flow_version_provider_info = {}
        schedule_logger(job.f_job_id).info(f'group_info:{provider_group}')
        for group_key, group_info in provider_group.items():
            if group_info["provider"]["name"] == ComponentProviderName.FATE_FLOW_TOOLS.value and \
                    group_info["provider"]["version"] not in fate_flow_version_provider_info:
                fate_flow_version_provider_info[group_info["provider"]["version"]] = group_info["provider"]
            if group_info["provider"]["name"] == ComponentProviderName.FATE_ALGORITHM.value and \
                    group_info["provider"]["version"] not in version_provider_info:
                version_provider_info[group_info["provider"]["version"]] = group_info["provider"]
            schedule_logger(job.f_job_id).info(f'version_provider_info:{version_provider_info}')
            schedule_logger(job.f_job_id).info(f'fate_flow_version_provider_info:{fate_flow_version_provider_info}')
        if not version_provider_info:
            version_provider_info = fate_flow_version_provider_info
        check_tag, upload_tag, upload_details = cls.check_upload(job.f_job_id, version_provider_info)
        if upload_tag:
            cls.upload_job_dependence(job, upload_details)
        return check_tag

    @classmethod
    def upload_job_dependence(cls, job, upload_details, storage_engine=FateDependenceStorageEngine.HDFS.value):
        schedule_logger(job.f_job_id).info(f"start upload dependence: {upload_details}")
        for version, type_provider in upload_details.items():
            for dependence_type, provider in type_provider.items():
                storage_meta = {
                    "f_storage_engine": storage_engine,
                    "f_type": dependence_type,
                    "f_version": version,
                    "f_upload_status": True
                }
                schedule_logger(job.f_job_id).info(f"update dependence storage meta:{storage_meta}")
                DependenceRegistry.save_dependencies_storage_meta(storage_meta, status_check=True)
                WorkerManager.start_general_worker(worker_name=WorkerName.DEPENDENCE_UPLOAD, job_id=job.f_job_id,
                                                   role=job.f_role, party_id=job.f_party_id, provider=provider,
                                                   dependence_type=dependence_type, callback=cls.record_upload_process,
                                                   callback_param=["dependence_type", "pid", "provider"])

    @classmethod
    def record_upload_process(cls, provider, dependence_type, pid, storage_engine=FateDependenceStorageEngine.HDFS.value):
        storage_meta = {
            "f_storage_engine": storage_engine,
            "f_type": dependence_type,
            "f_version": provider.version,
            "f_pid": pid,
            "f_upload_status": True
        }
        DependenceRegistry.save_dependencies_storage_meta(storage_meta)

    @classmethod
    def kill_upload_process(cls, version, storage_engine, dependence_type):
        storage_meta = {
            "f_storage_engine": storage_engine,
            "f_type": dependence_type,
            "f_version": version,
            "f_upload_status": False,
            "f_pid": 0
        }
        DependenceRegistry.save_dependencies_storage_meta(storage_meta)


    @classmethod
    def get_task_dependence_info(cls):
        return cls.get_executor_env_pythonpath(), cls.get_executor_python_env(), cls.get_driver_python_env(), \
               cls.get_archives()

    @classmethod
    def get_executor_env_pythonpath(cls):
        return cls.dependence_config.get(FateDependenceName.Fate_Source_Code.value).get("f_dependencies_conf").get(
            "executor_env_pythonpath")

    @classmethod
    def get_executor_python_env(cls):
        return cls.dependence_config.get(FateDependenceName.Python_Env.value).get("f_dependencies_conf").get(
            "executor_python")

    @classmethod
    def get_driver_python_env(cls):
        return cls.dependence_config.get(FateDependenceName.Python_Env.value).get("f_dependencies_conf").get(
            "driver_python")

    @classmethod
    def get_archives(cls, storage_engine=FateDependenceStorageEngine.HDFS.value):
        archives = []
        name_node = ResourceManager.get_engine_registration_info(engine_type=EngineType.STORAGE,
                                                                 engine_name=storage_engine
                                                                 ).f_engine_config.get("name_node")
        for dependence_type in [FateDependenceName.Fate_Source_Code.value, FateDependenceName.Python_Env.value]:
            archives.append(
                name_node + cls.dependence_config.get(dependence_type).get("f_dependencies_conf").get("archives")
            )
        return ','.join(archives)