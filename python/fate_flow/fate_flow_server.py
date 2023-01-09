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
# init env. must be the first import

import os
import signal
import sys
import traceback

import grpc
from grpc._cython import cygrpc
from werkzeug.serving import run_simple
from fate_flow.apps import app
from fate_flow.db.config_manager import ConfigManager
from fate_flow.runtime.runtime_config import RuntimeConfig
from fate_flow.db.base_models import init_database_tables as init_flow_db
from fate_flow.detection.detector import Detector, FederatedDetector
from fate_flow.entity.types import ProcessRole
from fate_flow.scheduler import init_scheduler
from fate_flow.scheduler.job_scheduler import DAGScheduler
from fate_flow.settings import (
    GRPC_PORT, GRPC_SERVER_MAX_WORKERS, HOST, HTTP_PORT, detect_logger, stat_logger,
)
from fate_flow.utils import process_utils
from fate_flow.utils.grpc_utils import UnaryService, UnaryServiceOSX
from fate_flow.utils.log_utils import schedule_logger, getLogger
from fate_flow.utils.version import get_versions
from fate_flow.utils.xthread import ThreadPoolExecutor
from fate_flow.proto.rollsite import proxy_pb2_grpc
from fate_flow.proto.osx import osx_pb2_grpc

if __name__ == '__main__':
    # init db
    signal.signal(signal.SIGCHLD, process_utils.wait_child_process)
    init_flow_db()
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
    RuntimeConfig.init_env()
    RuntimeConfig.init_config(JOB_SERVER_HOST=HOST, HTTP_PORT=HTTP_PORT)
    RuntimeConfig.set_process_role(ProcessRole.DRIVER)
    ConfigManager.load()
    init_scheduler()
    Detector(interval=5 * 1000, logger=detect_logger).start()
    FederatedDetector(interval=10 * 1000, logger=detect_logger).start()
    DAGScheduler(interval=2 * 1000, logger=schedule_logger()).start()
    thread_pool_executor = ThreadPoolExecutor(max_workers=GRPC_SERVER_MAX_WORKERS)
    stat_logger.info(f"start grpc server thread pool by {thread_pool_executor._max_workers} max workers")
    server = grpc.server(thread_pool=thread_pool_executor,
                         options=[(cygrpc.ChannelArgKey.max_send_message_length, -1),
                                  (cygrpc.ChannelArgKey.max_receive_message_length, -1)])
    osx_pb2_grpc.add_PrivateTransferProtocolServicer_to_server(UnaryServiceOSX(), server)
    proxy_pb2_grpc.add_DataTransferServiceServicer_to_server(UnaryService(), server)
    server.add_insecure_port(f"{HOST}:{GRPC_PORT}")
    server.start()
    print("FATE Flow grpc server start successfully")
    stat_logger.info("FATE Flow grpc server start successfully")

    # start http server
    try:
        print("FATE Flow http server start...")
        stat_logger.info("FATE Flow http server start...")
        werkzeug_logger = getLogger("werkzeug")
        run_simple(hostname=HOST, port=HTTP_PORT, application=app, threaded=True, use_reloader=RuntimeConfig.DEBUG, use_debugger=RuntimeConfig.DEBUG)
    except Exception:
        traceback.print_exc()
        os.kill(os.getpid(), signal.SIGKILL)
