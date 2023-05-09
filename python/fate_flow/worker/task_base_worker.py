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
import time

from fate_flow.db.runtime_config import RuntimeConfig
from fate_flow.entity.run_status import TaskStatus, EndStatus
from fate_flow.manager.pdsh_runner import PDSHRunner
from fate_flow.scheduling_apps.client import ControllerClient
from fate_flow.utils import task_utils
from fate_flow.utils.log_utils import getLogger
from fate_flow.worker.base_worker import BaseWorker


LOGGER = getLogger()


class ComponentInput:
    def __init__(
            self,
            tracker,
            checkpoint_manager,
            task_version_id,
            parameters,
            datasets,
            models,
            caches,
            job_parameters,
            roles,
            flow_feeded_parameters,
    ) -> None:
        self._tracker = tracker
        self._checkpoint_manager = checkpoint_manager
        self._task_version_id = task_version_id
        self._parameters = parameters
        self._datasets = datasets
        self._models = models
        self._caches = caches
        self._job_parameters = job_parameters
        self._roles = roles
        self._flow_feeded_parameters = flow_feeded_parameters

    @property
    def tracker(self):
        return self._tracker

    @property
    def task_version_id(self):
        return self._task_version_id

    @property
    def checkpoint_manager(self):
        return self._checkpoint_manager

    @property
    def parameters(self):
        return self._parameters

    @property
    def flow_feeded_parameters(self):
        return self._flow_feeded_parameters

    @property
    def roles(self):
        return self._roles

    @property
    def job_parameters(self):
        return self._job_parameters

    @property
    def datasets(self):
        return self._datasets

    @property
    def models(self):
        return {k: v for k, v in self._models.items() if v is not None}

    @property
    def caches(self):
        return self._caches


class BaseTaskWorker(BaseWorker):
    def _run(self):
        self.report_info.update({
            "job_id": self.args.job_id,
            "component_name": self.args.component_name,
            "task_id": self.args.task_id,
            "task_version": self.args.task_version,
            "role": self.args.role,
            "party_id": self.args.party_id,
            "run_ip": self.args.run_ip,
            "run_pid": self.run_pid
        })
        self._run_()

    def _run_(self):
        pass

    def _handle_exception(self):
        self.report_info["party_status"] = TaskStatus.FAILED
        self.report_task_info_to_driver()

    def report_task_info_to_driver(self):
        if self.need_report:
            LOGGER.info("report {} {} {} {} {} to driver:\n{}".format(
                self.__class__.__name__,
                self.report_info["task_id"],
                self.report_info["task_version"],
                self.report_info["role"],
                self.report_info["party_id"],
                self.report_info
            ))
            ControllerClient.report_task(self.report_info)
            self.sync_model()
            self.await_success()
            self.sync_logs()

    @property
    def need_report(self):
        report = False
        LOGGER.info(f"IS MASTER TASK: {os.getenv('IS_MASTER_TASK', 1)}")
        if int(os.getenv("IS_MASTER_TASK", 1)):
            # master task report
            report = True
        if self.report_info.get("party_status") in EndStatus.status_list():
            # All worker final states need to be reported
            report = True
        if os.getenv("LOCAL_RANK"):
            from fate_flow.entity.types import TaskLauncher
            self.report_info["launcher"] = TaskLauncher.PDSH.value
            self.report_info["rank"] = os.getenv("LOCAL_RANK")
            self.report_info["node"] = os.getenv("LOCAL_NODE")
        return report

    def await_success(self):
        # the master node task needs to wait for all tasks to succeed
        if self.is_master and self.report_info.get("party_status") == TaskStatus.SUCCESS:
            while True:
                LOGGER.info(f"master task wait until all other workers succeed")
                status = ControllerClient.query_task(self.report_info)
                LOGGER.info(f"task status: {status}")
                if status in EndStatus.status_list():
                    LOGGER.info(f"Task End!")
                    return
                time.sleep(5)

    def sync_logs(self):
        # The master worker not in fate flow server machine need sync logs to fate flow server
        if task_utils.is_master() and self.report_info.get("party_status") in EndStatus.status_list():
            if not task_utils.is_local_process():
                LOGGER.info("start sync logs")
                path = self.args.log_dir
                cmd = PDSHRunner().get_makedir_cmd(RuntimeConfig.JOB_SERVER_HOST, os.path.dirname(path))
                cmd = " ".join(cmd)
                LOGGER.info(f"mkdir cmd: {cmd}")
                f = os.popen(cmd)
                LOGGER.info(f"mkdir return: {f.read()}")

                cp_cmd = PDSHRunner().get_data_sync_cmd(RuntimeConfig.JOB_SERVER_HOST, path)
                cp_cmd = " ".join(cp_cmd)
                LOGGER.info(f"pdcp cmd: {cp_cmd}")
                f = os.popen(cp_cmd)
                LOGGER.info(f"pdcp return: {f.read()}")

    def sync_model(self):
        # The master worker not in fate flow server machine need sync model to fate flow server
        if task_utils.is_master() and self.report_info.get("party_status") == EndStatus.SUCCESS:
            if not task_utils.is_local_process():
                LOGGER.info("start sync model")
                model_dir = os.environ.get("MODEL_STORE_DIR")
                cmd = PDSHRunner().get_makedir_cmd(RuntimeConfig.JOB_SERVER_HOST, model_dir)
                cmd = " ".join(cmd)
                LOGGER.info(f"mkdir cmd: {cmd}")
                f = os.popen(cmd)
                LOGGER.info(f"mkdir return: {f.read()}")
                cp_cmd = PDSHRunner().get_data_sync_cmd(RuntimeConfig.JOB_SERVER_HOST, model_dir, base_dir=True)
                cp_cmd = " ".join(cp_cmd)
                LOGGER.info(f"pdcp cmd: {cp_cmd}")
                f = os.popen(cp_cmd)
                LOGGER.info(f"pdcp return: {f.read()}")
            else:
                LOGGER.info("The local directory does not need to be manipulated")
