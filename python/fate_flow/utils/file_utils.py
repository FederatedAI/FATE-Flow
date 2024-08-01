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

import json
import os
import uuid
from pathlib import Path

import pandas as pd
from ruamel import yaml
from sqlalchemy import create_engine

from fate_flow.runtime.env import is_in_virtualenv

PROJECT_BASE = os.getenv("FATE_PROJECT_BASE")
FATE_PYTHON_PATH = os.getenv("FATE_PYTHONPATH")


def get_project_base_directory(*args):
    global PROJECT_BASE
    if PROJECT_BASE is None:
        PROJECT_BASE = os.path.abspath(
            os.path.join(
                os.path.dirname(os.path.realpath(__file__)),
                os.pardir,
                os.pardir,
                os.pardir,
            )
        )
    if args:
        return os.path.join(PROJECT_BASE, *args)
    return PROJECT_BASE


def get_fate_python_path():
    global FATE_PYTHON_PATH
    if not FATE_PYTHON_PATH:
        FATE_PYTHON_PATH = get_project_base_directory("fate", "python")
        if not os.path.exists(FATE_PYTHON_PATH):
            FATE_PYTHON_PATH = get_project_base_directory("python")
            if not os.path.exists(FATE_PYTHON_PATH):
                return
    return FATE_PYTHON_PATH


def get_fate_flow_directory(*args):
    if is_in_virtualenv():
        fate_flow_dir = os.path.abspath(
            os.path.join(
                os.path.dirname(os.path.realpath(__file__)),
                os.pardir
            )
        )
    else:
        fate_flow_dir = os.path.abspath(
            os.path.join(
                os.path.dirname(os.path.realpath(__file__)),
                os.pardir,
                os.pardir,
                os.pardir,
            )
        )
    if args:
        return os.path.join(fate_flow_dir, *args)
    return fate_flow_dir


def transform_local_file(file):
    """
    Args:
        file (str):
            values like :
                mysql://user:password@host_ip:host_port/db/table
                file:///path/to/local_file.csv
                /path/to/local_file.csv
    """
    def _find_positions(s):
        last_at_index = s.rfind('@')
        first_colon_index = s.find(':')
        last_slash_index = s.rfind('/')
        second_last_slash_index = s.rfind('/', 0, last_slash_index)
        return last_at_index, first_colon_index, second_last_slash_index

    if file.startswith('mysql://'):
        db_info_str = file[8:]
        db_info = db_info_str.split('/')
        table_name = db_info[-1]
        dbname = db_info[-2]
        last_at, first_colon, second_last_slash = _find_positions(db_info_str)
        username = db_info_str[0:first_colon]
        password = db_info_str[first_colon + 1: last_at]
        host = db_info_str[last_at + 1:second_last_slash]
        database_url = f"mysql+pymysql://{username}:{password}@{host}/{dbname}"
        engine = create_engine(database_url)
        df = pd.read_sql_table(table_name, con=engine)
        file = f"/tmp/data_{uuid.uuid4()}.csv"
        df.to_csv(file, index=False)
        return file, True

    elif file.startswith('file://'):
        return file[7:], False

    else:
        return file, False


def file_delete(file):
    file_path = Path(file)
    file_path.unlink(missing_ok=True)


def load_yaml_conf(conf_path):
    if not os.path.isabs(conf_path):
        conf_path = os.path.join(get_fate_flow_directory(), conf_path)
    try:
        with open(conf_path) as f:
            return yaml.safe_load(f)
    except Exception as e:
        raise EnvironmentError(
            "loading yaml file config from {} failed:".format(conf_path), e
        )


def rewrite_json_file(filepath, json_data):
    with open(filepath, "w") as f:
        json.dump(json_data, f, indent=4, separators=(",", ": "))
    f.close()


def save_file(file, path):
    with open(path, 'wb') as f:
        content = file.stream.read()
        f.write(content)