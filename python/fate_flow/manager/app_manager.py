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
from fate_flow.db.base_models import BaseModelOperate
from fate_flow.db.db_models import AppInfo
from fate_flow.settings import ADMIN_KEY, ADMIN_ID, CLIENT_AUTHENTICATION
from fate_flow.utils.base_utils import generate_random_id
from fate_flow.utils.wraps_utils import filter_parameters


class AppManager(BaseModelOperate):
    @classmethod
    def init(cls):
        if CLIENT_AUTHENTICATION:
            if cls.query_app(app_name="admin"):
                cls._delete(AppInfo, app_name="admin")
            cls.create_app(app_name="admin", app_id="admin", app_token=ADMIN_KEY)

    @classmethod
    def create_app(cls, app_name, app_id=None, app_token=None):
        if not app_id:
            app_id = cls.generate_app_id()
        if not app_token:
            app_token = cls.generate_app_token()
        app_info = {
            "app_name": app_name,
            "app_id": app_id,
            "app_token": app_token
        }
        cls._create_entity(AppInfo, app_info)
        return app_info

    @classmethod
    @filter_parameters()
    def delete_app(cls, **kwargs):
        return cls._delete(AppInfo, **kwargs)

    @classmethod
    @filter_parameters()
    def query_app(cls, **kwargs):
        return cls._query(AppInfo, **kwargs)

    @classmethod
    def generate_app_id(cls, length=8):
        app_id = generate_random_id(length=length, only_number=True)
        if cls.query_app(app_id=app_id):
            cls.generate_app_id()
        else:
            return app_id

    @classmethod
    def generate_app_token(cls, length=10):
        return generate_random_id(length=length)
