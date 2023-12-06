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
import subprocess
import platform
import click
from ruamel import yaml

import fate_flow
from fate_flow.commands.service import manage_fate_service

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
HOME = os.path.dirname(fate_flow.__file__)
SERVER_CONF_PATH = os.path.join(HOME, "conf", "service_conf.yaml")
SETTING_PATH = os.path.join(HOME, "settings.py")
SERVICE_SH = os.path.join(HOME, "commands", "service.sh")


@click.group(short_help='Fate Flow', context_settings=CONTEXT_SETTINGS)
@click.pass_context
def flow_server_cli(ctx):
    '''
    Fate Flow server cli
    '''
    ctx.ensure_object(dict)
    if ctx.invoked_subcommand == 'init':
        return
    pass


@flow_server_cli.command('init', short_help='Flow Server init command')
@click.option('--ip', type=click.STRING, help='Fate flow server ip address.')
@click.option('--port', type=click.INT, help='Fate flow server http port.')
@click.option('--home', type=click.STRING, help="Service's home directory, used to store essential information "
                                                "such as data, logs, and more.")
def initialization(**kwargs):
    """
    \b
    - DESCRIPTION:
        Flow Init Command. provide ip and port of a valid fate flow server.

    \b
    - USAGE:
        fate_flow init --ip 127.0.0.1 --port 9380 --home /data/projects/fate_flow

    """
    init_server(kwargs.get("ip"), kwargs.get("port"), kwargs.get("home"))


@flow_server_cli.command('start', short_help='Start run flow server')
def start(**kwargs):
    """
    \b
    - DESCRIPTION:
        Start FATE Flow Server Command.

    \b
    - USAGE:
        fate_flow start

    """
    if platform.system().lower() == 'windows':
        manage_fate_service(HOME, "start")
    else:
        run_command("start")


@flow_server_cli.command('status', short_help='Query fate flow server status')
def status(**kwargs):
    """
    \b
    - DESCRIPTION:
        Query fate flow server status command

    \b
    - USAGE:
        fate_flow status

    """
    if platform.system().lower() == 'windows':
        manage_fate_service(HOME, "status")
    else:
        run_command("status")


@flow_server_cli.command('stop', short_help='Stop run flow server')
def stop(**kwargs):
    """
    \b
    - DESCRIPTION:
        Stop FATE Flow Server Command.

    \b
    - USAGE:
        fate_flow stop

    """
    if platform.system().lower() == 'windows':
        manage_fate_service(HOME, "stop")
    else:
        run_command("stop")


@flow_server_cli.command('restart', short_help='Restart fate flow server')
def restart(**kwargs):
    """
    \b
    - DESCRIPTION:
        ReStart FATE Flow Server Command.

    \b
    - USAGE:
        fate_flow restart

    """
    if platform.system().lower() == 'windows':
        manage_fate_service(HOME, "restart")
    else:
        run_command("restart")


@flow_server_cli.command('version', short_help='Flow Server Version Command')
def get_version():
    import fate_flow
    print(fate_flow.__version__)


def replace_settings(home_path):
    import re
    with open(SETTING_PATH, "r") as file:
        content = file.read()
    content = re.sub(r"DATA_DIR.*", f"DATA_DIR = \"{home_path}/data\"", content)
    content = re.sub(r"MODEL_DIR.*", f"MODEL_DIR = \"{home_path}/model\"", content)
    content = re.sub(r"JOB_DIR.*", f"JOB_DIR = \"{home_path}/jobs\"", content)
    content = re.sub(r"LOG_DIR.*", f"LOG_DIR = \"{home_path}/logs\"", content)
    content = re.sub(r"SQLITE_FILE_NAME.*", f"SQLITE_FILE_NAME = \"{home_path}/fate_flow_sqlite.db\"", content)
    with open(SETTING_PATH, "w") as file:
        file.write(content)

    with open(SERVICE_SH, "r") as file:
        content = file.read()
        content = re.sub(r"LOG_DIR.*=.*", f"LOG_DIR=\"{home_path}/logs\"", content)
    with open(SERVICE_SH, "w") as file:
        file.write(content)


def init_server(ip, port, home):
    with open(SERVER_CONF_PATH, "r") as file:
        config = yaml.safe_load(file)
    if ip:
        print(f"ip: {ip}")
        config["fateflow"]["host"] = ip
    if port:
        print(f"port: {port}")
        config["fateflow"]["http_port"] = port
    if home:
        if not os.path.isabs(home):
            raise RuntimeError(f"Please use an absolute path: {home}")
        os.makedirs(home, exist_ok=True)
        print(f"home: {home}")
        replace_settings(home)

    if ip or port:
        with open(SERVER_CONF_PATH, "w") as file:
            yaml.dump(config, file)

    print("Init server completed!")


def run_command(command):
    try:
        command = f"bash {SERVICE_SH} {HOME} {command}"
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, text=True)
        if result.returncode == 0:
            print(result.stdout)
            return result.stdout
        else:
            print(result.stdout)
            print(f"Error: {result.stderr}")
            return None
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        return command


if __name__ == '__main__':
    flow_server_cli()
