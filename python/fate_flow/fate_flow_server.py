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
import traceback

import grpc
from werkzeug.serving import run_simple

if __name__ == '__main__':
    from fate_flow.db.casbin_models import init_casbin
    init_casbin()

from fate_flow.apps import app
from fate_flow.manager.service.config_manager import ConfigManager
from fate_flow.hook import HookManager
from fate_flow.manager.service.app_manager import AppManager
from fate_flow.manager.service.provider_manager import ProviderManager
from fate_flow.manager.service.service_manager import service_db
from fate_flow.runtime.runtime_config import RuntimeConfig
from fate_flow.db.base_models import init_database_tables as init_flow_db
from fate_flow.scheduler.detector import Detector, FederatedDetector
from fate_flow.entity.types import ProcessRole
from fate_flow.scheduler import init_scheduler
from fate_flow.runtime.system_settings import (
    GRPC_PORT, GRPC_SERVER_MAX_WORKERS, HOST, HTTP_PORT , GRPC_OPTIONS, FATE_FLOW_LOG_DIR,
    LOG_LEVEL,
)
from fate_flow.scheduler.scheduler import DAGScheduler
from fate_flow.utils import process_utils
from fate_flow.utils.grpc_utils import UnaryService
from fate_flow.utils.log import LoggerFactory, getLogger
from fate_flow.utils.log_utils import schedule_logger
from fate_flow.utils.version import get_versions
from fate_flow.utils.xthread import ThreadPoolExecutor
from fate_flow.proto.rollsite import proxy_pb2_grpc

detect_logger = getLogger("fate_flow_detect")
stat_logger = getLogger("fate_flow_stat")


def server_init():
    # init logs
    LoggerFactory.set_directory(FATE_FLOW_LOG_DIR)
    LoggerFactory.LEVEL = LOG_LEVEL

    # set signal
    if "win" not in sys.platform.lower():
        signal.signal(signal.SIGCHLD, process_utils.wait_child_process)

    # init adapter
    try:
        from fate_flow.adapter import init_adapter
        init_adapter()
    except Exception as ex:
        stat_logger.exception(ex)

    # init db
    init_flow_db()

    # runtime config
    RuntimeConfig.init_env()
    RuntimeConfig.init_config(JOB_SERVER_HOST=HOST, HTTP_PORT=HTTP_PORT)
    RuntimeConfig.init_config()
    RuntimeConfig.set_service_db(service_db())
    RuntimeConfig.SERVICE_DB.register_flow()

    # manager
    ConfigManager.load()
    HookManager.init()
    AppManager.init()

    # scheduler
    init_scheduler()

    # detector
    Detector(interval=5 * 1000, logger=detect_logger).start()
    FederatedDetector(interval=10 * 1000, logger=detect_logger).start()
    DAGScheduler(interval=2 * 1000, logger=schedule_logger()).start()

    # provider register
    ProviderManager.register_default_providers()


def start_server(debug=False):
    # grpc
    thread_pool_executor = ThreadPoolExecutor(max_workers=GRPC_SERVER_MAX_WORKERS)
    stat_logger.info(f"start grpc server thread pool by {thread_pool_executor.max_workers} max workers")
    server = grpc.server(thread_pool=thread_pool_executor,
                         options=GRPC_OPTIONS)

    proxy_pb2_grpc.add_DataTransferServiceServicer_to_server(UnaryService(), server)
    server.add_insecure_port(f"{HOST}:{GRPC_PORT}")
    server.start()
    stat_logger.info("FATE Flow grpc server start successfully")

    # http
    stat_logger.info("FATE Flow http server start...")
    run_simple(
        hostname=HOST,
        port=HTTP_PORT,
        application=app,
        threaded=True,
        use_reloader=debug,
        use_debugger=debug
    )


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--version', default=False, help="fate flow version", action='store_true')
    parser.add_argument('--debug', default=False, help="debug mode", action='store_true')
    args = parser.parse_args()
    if args.version:
        print(get_versions())
        sys.exit(0)

    server_init()

    try:
        start_server(debug=args.debug)
    except Exception as e:
        traceback.print_exc()
        print(e)
        os.kill(os.getpid(), signal.SIGKILL)
