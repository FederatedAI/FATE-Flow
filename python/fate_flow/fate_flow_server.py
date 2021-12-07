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
import signal
import sys
import time
import traceback
import logging

import grpc
from grpc._cython import cygrpc
from werkzeug.serving import run_simple
# be sure to import environment variable before importing fate_arch
from fate_flow import set_env
from fate_arch.common import file_utils
from fate_flow.utils.base_utils import get_fate_flow_directory
from fate_flow.utils.proto_compatibility import proxy_pb2_grpc
from fate_flow.apps import app
from fate_flow.db.db_models import init_database_tables as init_flow_db
from fate_arch.metastore.db_models import init_database_tables as init_arch_db
from fate_flow.detection.detector import Detector
from fate_flow.scheduler.dag_scheduler import DAGScheduler
from fate_flow.db.runtime_config import RuntimeConfig
from fate_flow.entity.types import ProcessRole
from fate_flow.settings import (HOST, HTTP_PORT, GRPC_PORT, _ONE_DAY_IN_SECONDS, GRPC_SERVER_MAX_WORKERS,
                                stat_logger, detect_logger, access_logger, database_logger)
from fate_flow.utils.authentication_utils import PrivilegeAuth
from fate_flow.utils.grpc_utils import UnaryService
from fate_flow.db.db_services import service_db
from fate_flow.utils.xthread import ThreadPoolExecutor
from fate_flow.utils.log_utils import schedule_logger
from fate_arch.common.versions import get_versions
from fate_flow.db.config_manager import ConfigManager
from fate_flow.db.component_registry import ComponentRegistry
from fate_flow.manager.provider_manager import ProviderManager


if __name__ == '__main__':
    stat_logger.info(f"project base: {file_utils.get_project_base_directory()}, fate base: {file_utils.get_fate_directory()}, fate flow base: {get_fate_flow_directory()}")
    # init
    # signal.signal(signal.SIGTERM, job_utils.cleaning)
    # signal.signal(signal.SIGCHLD, process_utils.wait_child_process)
    # init db
    init_flow_db()
    init_arch_db()
    # init runtime config
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--version', default=False, help="fate flow version", action='store_true')
    parser.add_argument('--debug', default=False, help="debug mode", action='store_true')
    args = parser.parse_args()
    if args.version:
        print(get_versions())
        sys.exit(0)
    # todo: add a general init steps?
    RuntimeConfig.DEBUG = args.debug
    if RuntimeConfig.DEBUG:
        stat_logger.info("run on debug mode")
    ConfigManager.load()
    RuntimeConfig.init_env()
    RuntimeConfig.init_config(JOB_SERVER_HOST=HOST, HTTP_PORT=HTTP_PORT)
    RuntimeConfig.set_process_role(ProcessRole.DRIVER)

    RuntimeConfig.set_service_db(service_db())
    RuntimeConfig.SERVICE_DB.register_flow()
    RuntimeConfig.SERVICE_DB.register_models()

    ComponentRegistry.load()
    default_algorithm_provider = ProviderManager.register_default_providers()
    RuntimeConfig.set_component_provider(default_algorithm_provider)
    ComponentRegistry.load()
    PrivilegeAuth.init()
    Detector(interval=5 * 1000, logger=detect_logger).start()
    DAGScheduler(interval=2 * 1000, logger=schedule_logger()).start()

    peewee_logger = logging.getLogger('peewee')
    peewee_logger.propagate = False
    # fate_arch.common.log.ROpenHandler
    peewee_logger.addHandler(database_logger.handlers[0])
    peewee_logger.setLevel(database_logger.level)

    thread_pool_executor = ThreadPoolExecutor(max_workers=GRPC_SERVER_MAX_WORKERS)
    stat_logger.info(f"start grpc server thread pool by {thread_pool_executor._max_workers} max workers")
    server = grpc.server(thread_pool=thread_pool_executor,
                         options=[(cygrpc.ChannelArgKey.max_send_message_length, -1),
                                  (cygrpc.ChannelArgKey.max_receive_message_length, -1)])

    proxy_pb2_grpc.add_DataTransferServiceServicer_to_server(UnaryService(), server)
    server.add_insecure_port("{}:{}".format(HOST, GRPC_PORT))
    server.start()
    print("FATE Flow grpc server start successfully")
    stat_logger.info("FATE Flow grpc server start successfully")

    # start http server
    try:
        print("FATE Flow http server start...")
        stat_logger.info("FATE Flow http server start...")
        werkzeug_logger = logging.getLogger("werkzeug")
        for h in access_logger.handlers:
            werkzeug_logger.addHandler(h)
        run_simple(hostname=HOST, port=HTTP_PORT, application=app, threaded=True, use_reloader=RuntimeConfig.DEBUG, use_debugger=RuntimeConfig.DEBUG)
    except OSError as e:
        traceback.print_exc()
        os.kill(os.getpid(), signal.SIGKILL)
    except Exception as e:
        traceback.print_exc()
        os.kill(os.getpid(), signal.SIGKILL)

    try:
        while True:
            time.sleep(_ONE_DAY_IN_SECONDS)
    except KeyboardInterrupt:
        server.stop(0)
        sys.exit(0)
