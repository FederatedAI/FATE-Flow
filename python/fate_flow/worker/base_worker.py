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
import os
import sys
import traceback

from fate_arch.common.base_utils import current_timestamp
from fate_arch.common.file_utils import load_json_conf, dump_json_conf
from fate_flow.utils.log_utils import getLogger, LoggerFactory
from fate_flow.db.component_registry import ComponentRegistry
from fate_flow.db.config_manager import ConfigManager
from fate_flow.db.runtime_config import RuntimeConfig
from fate_flow.entity.types import ProcessRole
from fate_flow.entity import BaseEntity

LOGGER = getLogger()


class WorkerArgs(BaseEntity):
    def __init__(self, **kwargs):
        self.job_id = kwargs.get("job_id")
        self.component_name = kwargs.get("component_name")
        self.task_id = kwargs.get("task_id")
        self.task_version = kwargs.get("task_version")
        self.role = kwargs.get("role")
        self.party_id = kwargs.get("party_id")
        self.config = self.load_dict_attr(kwargs, "config")
        self.result = kwargs.get("result")
        self.log_dir = kwargs.get("log_dir")
        self.parent_log_dir = kwargs.get("parent_log_dir")

        self.run_ip = kwargs.get("run_ip")
        self.job_server = kwargs.get("job_server")

        # TaskInitializer
        self.result = kwargs.get("result")
        self.dsl = self.load_dict_attr(kwargs, "dsl")
        self.runtime_conf = self.load_dict_attr(kwargs, "runtime_conf")
        self.train_runtime_conf = self.load_dict_attr(kwargs, "train_runtime_conf")
        self.pipeline_dsl = self.load_dict_attr(kwargs, "pipeline_dsl")

        # TaskSender & TaskReceiver
        self.session_id = kwargs.get("session_id")
        self.federation_session_id = kwargs.get("federation_session_id")

        # TaskSender
        self.receive_topic = kwargs.get("receive_topic")

        # TaskReceiver
        self.http_port = kwargs.get("http_port")
        self.grpc_port = kwargs.get("grpc_port")

    def load_dict_attr(self, kwargs: dict, attr_name: str):
        return load_json_conf(kwargs[attr_name]) if kwargs.get(attr_name) else {}


class BaseWorker:
    def __init__(self):
        self.args: WorkerArgs = None
        self.run_pid = None
        self.report_info = {}

    def run(self, **kwargs):
        result = None
        start_time = current_timestamp()
        self.run_pid = os.getpid()
        try:
            self.args = self.get_args(**kwargs)
            LoggerFactory.set_directory(directory=self.args.log_dir, parent_log_dir=self.args.parent_log_dir,
                                        append_to_parent_log=True, force=True)
            LOGGER.info(f"enter {self.__class__.__name__} worker process, pid: {self.run_pid}")
            for env in {"VIRTUAL_ENV", "PYTHONPATH", "SPARK_HOME", "FATE_DEPLOY_BASE", "FATE_JOB_ID"}:
                LOGGER.info(f"{env}: {os.getenv(env)}")
            if self.args.job_server:
                RuntimeConfig.init_config(JOB_SERVER_HOST=self.args.job_server.split(':')[0],
                                          HTTP_PORT=self.args.job_server.split(':')[1])
            RuntimeConfig.set_process_role(ProcessRole.WORKER)
            # todo: get conf from server
            ConfigManager.load()
            ComponentRegistry.load()
            result = self._run(**kwargs)
            sys.exit(0)
        except Exception as e:
            LOGGER.exception(e)
            traceback.print_exc()
            try:
                self._handle_exception()
            except Exception as e:
                LOGGER.exception(e)
            sys.exit(1)
        finally:
            if not result:
                result = {}
            if self.args and self.args.result:
                dump_json_conf(result, self.args.result)
            end_time = current_timestamp()
            LOGGER.info(f"worker {self.__class__.__name__}, pid: {self.run_pid}, elapsed: {end_time - start_time} ms")

    def _run(self, **kwargs):
        raise NotImplementedError

    def _handle_exception(self):
        pass

    def get_args(self, **kwargs):
        if kwargs:
            return WorkerArgs(**kwargs)
        else:
            parser = argparse.ArgumentParser()
            for arg in WorkerArgs().to_dict():
                parser.add_argument(f"--{arg}", required=False)
            return WorkerArgs(**parser.parse_args().__dict__)
