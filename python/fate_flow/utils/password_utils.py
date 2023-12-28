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
import os.path
from importlib import import_module

from fate_flow.runtime.system_settings import ENCRYPT_CONF
from fate_flow.utils.conf_utils import conf_realpath


def decrypt_database_config(database, passwd_key="passwd", decrypt_key=""):
    database[passwd_key] = decrypt_password(database[passwd_key], key=decrypt_key)
    return database


def decrypt_password(password, key=""):
    if not ENCRYPT_CONF or not key or key not in ENCRYPT_CONF:
        return password
    encrypt_module = ENCRYPT_CONF.get(key).get("module", "")
    private_path = ENCRYPT_CONF.get(key).get("private_path", "")
    if not encrypt_module:
        raise ValueError(f"module is {encrypt_module}")
    if not private_path:
        raise ValueError(f"private_path is {private_path}")
    if not os.path.isabs(private_path):
        private_path = conf_realpath(private_path)
    with open(private_path) as f:
        private_key = f.read()
    module_func = encrypt_module.split("#")
    encrypt_func = getattr(import_module(module_func[0]), module_func[1])
    return encrypt_func(private_key, password)
