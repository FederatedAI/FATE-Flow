import os
import sys

from fate_arch import storage
from fate_arch.common import EngineType
from fate_flow.controller.job_controller import JobController
from fate_flow.entity.run_status import JobInheritanceStatus, TaskStatus
from fate_flow.operation.job_saver import JobSaver
from fate_flow.utils.log_utils import schedule_logger
from fate_arch.computing import ComputingEngine
from fate_flow.db.dependence_registry import DependenceRegistry
from fate_flow.entity import ComponentProvider
from fate_flow.entity.types import FateDependenceName, ComponentProviderName, FateDependenceStorageEngine, WorkerName
from fate_flow.manager.provider_manager import ProviderManager
from fate_flow.manager.worker_manager import WorkerManager
from fate_flow.settings import DEPENDENT_DISTRIBUTION, FATE_FLOW_UPDATE_CHECK, ENGINES
from fate_flow.utils import schedule_utils, job_utils, process_utils
from fate_flow.worker.job_inheritor import JobInherit


class DependenceManager:
    @classmethod
    def check_job_dependence(cls, job):
        if cls.check_job_inherit_dependence(job) and cls.check_spark_dependence(job):
            return True
        else:
            return False

    @classmethod
    def check_job_inherit_dependence(cls, job):
        schedule_logger(job.f_job_id).info(
            f"check job inherit dependence: {job.f_inheritance_info}, {job.f_inheritance_status}")
        if job.f_inheritance_info:
            if job.f_inheritance_status == JobInheritanceStatus.WAITING:
                cls.start_inheriting_job(job)
                return False
            elif job.f_inheritance_status == JobInheritanceStatus.RUNNING:
                return False
            elif job.f_inheritance_status == JobInheritanceStatus.FAILED:
                raise Exception("job inheritance failed")
            else:
                return True
        else:
            return True

    @classmethod
    def component_check(cls, job, check_type="inheritance"):
        if check_type == "rerun":
            task_list = JobSaver.query_task(job_id=job.f_job_id, party_id=job.f_party_id, role=job.f_role,
                                            status=TaskStatus.SUCCESS, only_latest=True)
            tasks = {}
            for task in task_list:
                tasks[task.f_component_name] = task
        else:
            tasks = JobController.load_tasks(component_list=job.f_inheritance_info.get("component_list", []),
                                             job_id=job.f_inheritance_info.get("job_id"),
                                             role=job.f_role,
                                             party_id=job.f_party_id)
        tracker_dict = JobController.load_task_tracker(tasks)
        missing_dependence_component_list = []
        # data dependence
        for tracker in tracker_dict.values():
            table_infos = tracker.get_output_data_info()
            for table in table_infos:
                table_meta = storage.StorageTableMeta(name=table.f_table_name, namespace=table.f_table_namespace)
                if not table_meta:
                    missing_dependence_component_list.append(tracker.component_name)
                    continue
        if check_type == "rerun":
            return missing_dependence_component_list
        elif check_type == "inheritance":
            # reload component list
            return list(set(job.f_inheritance_info.get("component_list", [])) - set(missing_dependence_component_list))

    @classmethod
    def start_inheriting_job(cls, job):
        JobSaver.update_job(job_info={"job_id": job.f_job_id, "role": job.f_role, "party_id": job.f_party_id,
                                      "inheritance_status": JobInheritanceStatus.RUNNING})
        conf_dir = job_utils.get_job_directory(job_id=job.f_job_id)
        os.makedirs(conf_dir, exist_ok=True)
        process_cmd = [
            sys.executable or 'python3',
            sys.modules[JobInherit.__module__].__file__,
            '--job_id', job.f_job_id,
            '--role', job.f_role,
            '--party_id', job.f_party_id,
        ]
        log_dir = os.path.join(job_utils.get_job_log_directory(job_id=job.f_job_id), "job_inheritance")
        p = process_utils.run_subprocess(job_id=job.f_job_id, config_dir=conf_dir, process_cmd=process_cmd,
                                         log_dir=log_dir, process_name="job_inheritance")

    @classmethod
    def check_spark_dependence(cls, job):
        if not DEPENDENT_DISTRIBUTION:
            return True
        engine_name = ENGINES.get(EngineType.COMPUTING)
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
            if group_info["provider"]["name"] == ComponentProviderName.FATE_FLOW.value and \
                    group_info["provider"]["version"] not in fate_flow_version_provider_info:
                fate_flow_version_provider_info[group_info["provider"]["version"]] = group_info["provider"]
            if group_info["provider"]["name"] == ComponentProviderName.FATE.value and \
                    group_info["provider"]["version"] not in version_provider_info:
                version_provider_info[group_info["provider"]["version"]] = group_info["provider"]
            schedule_logger(job.f_job_id).info(f'version_provider_info:{version_provider_info}')
            schedule_logger(job.f_job_id).info(f'fate_flow_version_provider_info:{fate_flow_version_provider_info}')
        if not version_provider_info:
            version_provider_info = fate_flow_version_provider_info
        check_tag, upload_tag, upload_details = cls.check_upload(job.f_job_id, version_provider_info,
                                                                 fate_flow_version_provider_info)
        if upload_tag:
            cls.upload_spark_dependence(job, upload_details)
        return check_tag

    @classmethod
    def check_upload(cls, job_id, provider_group, fate_flow_version_provider_info,
                     storage_engine=FateDependenceStorageEngine.HDFS.value):
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

                    elif dependence_type == FateDependenceName.Fate_Source_Code.value:
                        if provider.name == ComponentProviderName.FATE.value:
                            check_fate_flow_provider_status = False
                            if fate_flow_version_provider_info.values():
                                flow_provider = ComponentProvider(**list(fate_flow_version_provider_info.values())[0])
                                check_fate_flow_provider_status = DependenceRegistry.get_modify_time(flow_provider.path) \
                                                                  != dependencies_storage_info.f_fate_flow_snapshot_time
                            if FATE_FLOW_UPDATE_CHECK and check_fate_flow_provider_status:
                                need_upload = True
                                upload_total += 1
                            elif DependenceRegistry.get_modify_time(provider.path) != \
                                    dependencies_storage_info.f_snapshot_time:
                                need_upload = True
                                upload_total += 1
                        elif provider.name == ComponentProviderName.FATE_FLOW.value and FATE_FLOW_UPDATE_CHECK:
                            if DependenceRegistry.get_modify_time(provider.path) != \
                                    dependencies_storage_info.f_fate_flow_snapshot_time:
                                need_upload = True
                                upload_total += 1
                else:
                    need_upload = True
                    upload_total += 1
                if need_upload:
                    upload_details[version][dependence_type] = provider
        if upload_total > 0:
            check_tag = False
        schedule_logger(job_id).info(f"check dependencies result: {check_tag}, {upload_details}")
        return check_tag, upload_total > 0, upload_details

    @classmethod
    def upload_spark_dependence(cls, job, upload_details, storage_engine=FateDependenceStorageEngine.HDFS.value):
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
    def record_upload_process(cls, provider, dependence_type, pid,
                              storage_engine=FateDependenceStorageEngine.HDFS.value):
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
