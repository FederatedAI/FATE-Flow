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
import hashlib
import time

from fate_flow.db.casbin_models import FATE_CASBIN
from fate_flow.errors.server_error import RequestExpired, NoFoundAppid, InvalidParameter, RoleTypeError
from fate_flow.manager.service.app_manager import AppManager
from fate_flow.runtime.runtime_config import RuntimeConfig
from fate_flow.runtime.system_settings import CLIENT_AUTHENTICATION, SITE_AUTHENTICATION
from fate_flow.utils.base_utils import generate_random_id
from fate_flow.utils.wraps_utils import switch_function,  check_permission


class Authentication(object):
    @classmethod
    def md5_sign(cls, app_id, app_token, user_name, initiator_party_id, timestamp, nonce):
        key = hashlib.md5(str(app_id + user_name + initiator_party_id + nonce + timestamp).encode("utf8")).hexdigest().lower()
        sign = hashlib.md5(str(key + app_token).encode("utf8")).hexdigest().lower()
        return sign

    @classmethod
    def md5_verify(cls, app_id, timestamp, nonce, signature, user_name="", initiator_party_id=""):
        if cls.check_if_expired(timestamp):
            raise RequestExpired()
        apps = AppManager.query_app(app_id=app_id)
        if apps:
            _signature = cls.md5_sign(
                app_id=app_id,
                app_token=apps[0].f_app_token,
                user_name=user_name,
                initiator_party_id=initiator_party_id,
                timestamp=timestamp,
                nonce=nonce
            )
            return _signature == signature
        else:
            raise NoFoundAppid(app_id=app_id)

    @staticmethod
    def generate_timestamp():
        return str(int(time.time()*1000))

    @staticmethod
    def generate_nonce():
        return generate_random_id(length=4, only_number=True)

    @staticmethod
    def check_if_expired(timestamp, timeout=60):
        expiration = int(timestamp) + timeout * 1000
        if expiration < int(time.time() * 1000):
            return True
        else:
            return False


class PermissionController(object):
    @staticmethod
    @switch_function(CLIENT_AUTHENTICATION or SITE_AUTHENTICATION)
    def add_policy(role, resource, permission):
        return FATE_CASBIN.add_policy(role, resource, permission)

    @staticmethod
    @switch_function(CLIENT_AUTHENTICATION or SITE_AUTHENTICATION)
    @AppManager.check_app_id
    @check_permission(operate="grant", types="permission")
    @AppManager.check_app_type
    def add_role_for_user(app_id, role, init=False):
        PermissionController.check_permission_role(role)
        return FATE_CASBIN.add_role_for_user(app_id, role)

    @staticmethod
    @switch_function(CLIENT_AUTHENTICATION or SITE_AUTHENTICATION)
    @AppManager.check_app_id
    @check_permission(operate="delete", types="permission")
    # @AppManager.check_app_type
    def delete_role_for_user(app_id, role, grant_role=None, init=False):
        role_type = role
        PermissionController.check_permission_role(role)
        app_info = AppManager.query_app(app_id=app_id)
        if grant_role == "super_client":
            grant_role = "client"
        if grant_role and grant_role != app_info[0].f_app_type:
            raise RoleTypeError(role=grant_role)
        return FATE_CASBIN.delete_role_for_suer(app_id, role_type)

    @staticmethod
    @switch_function(CLIENT_AUTHENTICATION or SITE_AUTHENTICATION)
    @AppManager.check_app_id
    @check_permission(operate="query", types="permission")
    def get_roles_for_user(app_id):
        return FATE_CASBIN.get_roles_for_user(app_id)

    @staticmethod
    @switch_function(CLIENT_AUTHENTICATION or SITE_AUTHENTICATION)
    def get_permissions_for_user(app_id):
        return FATE_CASBIN.get_permissions_for_user(app_id)

    @staticmethod
    @switch_function(CLIENT_AUTHENTICATION or SITE_AUTHENTICATION)
    @AppManager.check_app_id
    def delete_roles_for_user(app_id):
        return FATE_CASBIN.delete_roles_for_user(app_id)

    @staticmethod
    @switch_function(CLIENT_AUTHENTICATION or SITE_AUTHENTICATION)
    @AppManager.check_app_id
    def has_role_for_user(app_id, role):
        return FATE_CASBIN.has_role_for_user(app_id, role)

    @staticmethod
    @switch_function(CLIENT_AUTHENTICATION or SITE_AUTHENTICATION)
    @AppManager.check_app_id
    def enforcer(app_id, resource, permission):
        return FATE_CASBIN.enforcer(app_id, resource, permission)

    @staticmethod
    def check_permission_role(role):
        if role not in RuntimeConfig.CLIENT_ROLE:
            raise InvalidParameter(role=role)
