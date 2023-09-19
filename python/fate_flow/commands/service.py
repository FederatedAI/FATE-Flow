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
import subprocess
import time
from ruamel import yaml


def load_yaml_conf(conf_path):
    with open(conf_path) as f:
        return yaml.safe_load(f)


def make_logs_dir(log_dir):
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)


def manage_fate_service(project_base, action):
    parser = argparse.ArgumentParser(description='FATE Service Manager')
    parser.add_argument('project_base', type=str, help='path to the FATE project directory')
    parser.add_argument('action', choices=['start', 'stop', 'status', 'restart'], help='action to perform')

    args = parser.parse_args([project_base, action])
    print(f'project_base:{args.project_base},action:{args.action}')
    http_port, grpc_port = get_ports(args.project_base)
    if args.action == 'start':
        start_service(args.project_base)
        get_service_status(http_port, grpc_port)
    elif args.action == 'stop':
        stop_service(http_port, grpc_port)
    elif args.action == 'status':
        get_service_status(http_port, grpc_port)
    elif args.action == 'restart':
        stop_service(http_port, grpc_port)
        time.sleep(2)
        start_service(args.project_base)
        get_service_status(http_port, grpc_port)


def get_ports(project_base):
    service_conf_path = os.path.join(project_base, 'conf/service_conf.yaml')
    if not os.path.isfile(service_conf_path):
        print(f'service conf not found: {service_conf_path}')
        exit(1)

    config = load_yaml_conf(service_conf_path)
    http_port = config.get('fateflow').get('http_port')
    grpc_port = config.get('fateflow').get('grpc_port')
    print(f'fate flow http port: {http_port}, grpc port: {grpc_port}\n')
    return http_port, grpc_port


def get_pid(http_port, grpc_port):
    netstat_command = ["netstat", "-ano"]
    output = subprocess.run(netstat_command, capture_output=True, text=True).stdout

    pid = None
    lines = output.split('\n')
    for line in lines:
        parts = line.split()
        if len(parts) >= 5:
            protocol = parts[0]
            local_address = parts[1]
            state = parts[3]
            if state == 'LISTENING' and ':' in local_address:
                port = local_address.split(':')[-1]
                _pid = parts[-1]
                if port == str(http_port) or port == str(grpc_port):
                    pid = _pid
                    break
    return pid


def get_service_status(http_port, grpc_port):
    pid = get_pid(http_port, grpc_port)
    if pid:
        task_list = subprocess.getoutput(f"tasklist /FI \"PID eq {pid}\"")
        print(f"status: {task_list}")

        print(f'LISTENING on port {http_port}:')
        print(subprocess.getoutput(f'netstat -ano | findstr :{http_port}'))

        print(f'LISTENING on port {grpc_port}:')
        print(subprocess.getoutput(f'netstat -ano | findstr :{grpc_port}'))
    else:
        print('service not running')


def start_service(project_base):
    http_port = None
    grpc_port = None

    service_conf_path = os.path.join(project_base, 'conf/service_conf.yaml')
    if os.path.isfile(service_conf_path):
        config = load_yaml_conf(service_conf_path)
        http_port = config.get('fateflow').get('http_port')
        grpc_port = config.get('fateflow').get('grpc_port')

    if not http_port or not grpc_port:
        print(f'service conf not found or missing port information: {service_conf_path}')
        exit(1)

    pid = get_pid(http_port, grpc_port)
    if pid:
        print(f'service already started. pid: {pid}')
        return

    log_dir = os.path.join(project_base, 'logs')
    make_logs_dir(log_dir)

    command = ['python', os.path.join(project_base, 'fate_flow_server.py')]
    # print(f'command:{command}')
    stdout = open(os.path.join(log_dir, 'console.log'), 'a')
    stderr = open(os.path.join(log_dir, 'error.log'), 'a')

    subprocess.Popen(command, stdout=stdout, stderr=stderr)

    for _ in range(100):
        time.sleep(0.1)
        pid = get_pid(http_port, grpc_port)
        if pid:
            print(f'service started successfully. pid: {pid}')
            return

    pid = get_pid(http_port, grpc_port)
    if pid:
        print(f'service started successfully. pid: {pid}')
    else:
        print(
            f'service start failed, please check {os.path.join(log_dir, "error.log")} and {os.path.join(log_dir, "console.log")}')


def stop_service(http_port, grpc_port):
    pid = get_pid(http_port, grpc_port)
    if not pid:
        print('service not running')
        return
    task_list = subprocess.getoutput(f"tasklist /FI \"PID eq {pid}\"")
    print(f'killing: {task_list}')

    try:
        subprocess.run(['taskkill', '/F', '/PID', str(pid)])
        time.sleep(1)
    except subprocess.CalledProcessError:
        print('failed to kill the process')
        return

    if get_pid(http_port, grpc_port):
        print('failed to stop the service')
    else:
        print('service stopped successfully')




