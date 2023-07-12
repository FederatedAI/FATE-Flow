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
from peewee import Insert

from fate_flow.runtime.system_settings import SQLITE_PATH


def get_database_connection(config, decrypt_key):
    Insert.on_conflict = lambda self, *args, **kwargs: self.on_conflict_replace()
    from playhouse.apsw_ext import APSWDatabase
    path = config.get("path")
    if not path:
        path = SQLITE_PATH
    return APSWDatabase(path)
