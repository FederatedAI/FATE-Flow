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

from fate_flow.db.casbin_models import FATE_CASBIN, PERMISSION_CASBIN as PC
from fate_flow.errors.server_error import NoPermission, PermissionOperateError
from fate_flow.manager.service.provider_manager import ProviderManager
from fate_flow.utils.log_utils import getLogger
from fate_flow.entity.types import PermissionParameters, DataSet, PermissionType
from fate_flow.hook.common.parameters import PermissionReturn
from fate_flow.errors.server_error import RequestExpired, NoFoundAppid, InvalidParameter, RoleTypeError
from fate_flow.manager.service.app_manager import AppManager
from fate_flow.runtime.runtime_config import RuntimeConfig
from fate_flow.runtime.system_settings import CLIENT_AUTHENTICATION, SITE_AUTHENTICATION
from fate_flow.utils.base_utils import generate_random_id
from fate_flow.utils.wraps_utils import switch_function,  check_permission

logger = getLogger("permission")


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


class ResourcePermissionController:
    def __init__(self, party_id):
        self.party_id = party_id
        self.casbin_controller = PC
        if not self.casbin_controller:
            raise PermissionOperateError(message="No permission controller is found")

    def check(self, permission_type, value):
        logger.info(f"check source party id {self.party_id} {permission_type} {value}")
        result = self.casbin_controller.enforce(self.party_id, permission_type, value)
        logger.info(f"result: {result}")
        return result

    def grant_or_delete(self, permission_parameters: PermissionParameters):
        logger.info(f"{'grant' if not permission_parameters.is_delete else 'delete'} parameters:"
                    f" {permission_parameters.to_dict()}")
        self.check_parameters(permission_parameters)
        for permission_type in PermissionType.values():
            permission_value = getattr(permission_parameters, permission_type)
            if permission_value:
                if permission_value != "*":
                    if permission_type in [PermissionType.COMPONENT.value]:
                        value_list = [value.strip() for value in permission_value.split(self.value_delimiter)]
                    elif permission_type in [PermissionType.DATASET.value]:
                        if isinstance(permission_value, list):
                            value_list = [DataSet(**value).casbin_value for value in permission_value]
                        else:
                            value_list = [DataSet(**permission_value).casbin_value]
                    else:
                        raise PermissionOperateError(type=permission_type, message="Not Supported")
                    for value in value_list:
                        if not permission_parameters.is_delete:
                            self.casbin_controller.grant(self.party_id, permission_type, value)
                        else:
                            self.casbin_controller.delete(self.party_id, permission_type, value)
                else:
                    if not permission_parameters.is_delete:
                        for value in self.all_value(permission_type):
                            self.casbin_controller.grant(self.party_id, permission_type, value)
                    else:
                        self.casbin_controller.delete_all(self.party_id, permission_type)

    def query(self):
        result = {PermissionType.DATASET.value: [], PermissionType.COMPONENT.value: []}
        for casbin_result in self.casbin_controller.query(self.party_id):
            if casbin_result[1] == PermissionType.DATASET.value:
                casbin_result[2] = DataSet.load_casbin_value(casbin_result[2])
            result[casbin_result[1]].append(casbin_result[2])
        return result

    def check_parameters(self, permission_parameters):
        for permission_type in PermissionType.values():
            permission_value = getattr(permission_parameters, permission_type)
            if permission_value:
                if permission_type in [PermissionType.COMPONENT.value]:
                    if permission_value != "*":
                        value_list = [value.strip() for value in permission_value.split(self.value_delimiter)]
                        self.check_values(permission_type, value_list)
                if permission_type in [PermissionType.DATASET.value]:
                    if isinstance(permission_value, list):
                        for dataset in permission_value:
                            DataSet(**dataset).check()
                    elif isinstance(permission_value, dict):
                        DataSet(**permission_value).check()
                    elif permission_value == "*":
                        pass
                    else:
                        raise PermissionOperateError(type=permission_type, value=permission_value)

    def check_values(self, permission_type, values):
        error_value = []
        value_list = self.all_value(permission_type)
        for value in values:
            if value not in value_list:
                error_value.append(value)
        if error_value:
            raise PermissionOperateError(type=permission_type, value=error_value)

    def all_value(self, permission_type):
        if permission_type == PermissionType.COMPONENT.value:
            value_list = self.all_component
        else:
            raise PermissionOperateError(type=permission_type, message="Not Support Grant all")
        return value_list

    @property
    def all_component(self):
        return ProviderManager.get_all_components()

    @property
    def value_delimiter(self):
        return ","


class PermissionCheck(object):
    def __init__(self, party_id, component_list, dataset_list, **kwargs):
        self.component_list = component_list
        self.dataset_list = dataset_list
        self.controller = ResourcePermissionController(party_id)

    def check_component(self) -> PermissionReturn:
        for component_name in self.component_list:
            if not self.controller.check(PermissionType.COMPONENT.value, component_name):
                e = NoPermission(type=PermissionType.COMPONENT.value, component_name=component_name)
                return PermissionReturn(code=e.code, message=e.message)
        return PermissionReturn()

    def check_dataset(self) -> PermissionReturn:
        for dataset in self.dataset_list:
            if not self.controller.check(PermissionType.DATASET.value, dataset.casbin_value):
                e = NoPermission(type=PermissionType.DATASET.value, dataset=dataset.value)
                return PermissionReturn(e.code, e.message)
        return PermissionReturn()
