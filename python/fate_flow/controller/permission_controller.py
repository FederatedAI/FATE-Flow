import time

from fate_flow.utils.log_utils import getLogger
from fate_flow.db.db_models import PermissionStorage, DB
from fate_flow.entity.permission_parameters import PermissionParameters, DataSet, CheckReturn
from fate_flow.entity.types import PermissionType, ComponentProviderName
from fate_flow.hook.parameters import PermissionReturn
from fate_flow.settings import DATASET_PERMISSION, ROLE_PERMISSION, COMPONENT_PERMISSION

logger = getLogger("permission")


class PermissionController:
    def __init__(self, src_role, src_party_id):
        self.src_role = src_role
        self.src_party_id = src_party_id

    def check(self, permission_type, value):
        logger.info(f"check source role {self.src_role} party id {self.src_party_id} {permission_type} {value}")
        result = self.query(permission_type=permission_type, value=value)
        logger.info(f"result: {result}")
        if result:
            expire_time = result[permission_type][0][1]
            if expire_time and expire_time < time.time():
                return False
            return True
        return False

    def grant_or_delete(self, permission_parameters: PermissionParameters):
        logger.info(f"{'grant' if not permission_parameters.is_delete else 'delete'} parameters:"
                    f" {permission_parameters.to_dict()}")
        self.check_parameters(permission_parameters)
        for permission_type in PermissionType.values():
            permission_value = getattr(permission_parameters, permission_type)
            if permission_value:
                if permission_value != "*":
                    if permission_type in [PermissionType.ROLE.value, PermissionType.COMMAND.value, PermissionType.COMPONENT.value]:
                        value_list = [value.strip() for value in permission_value.split(self.value_delimiter)]
                    elif permission_type in [PermissionType.DATASET.value]:
                        if isinstance(permission_value, list):
                            value_list = [DataSet(**value).value for value in permission_value]
                        else:
                            value_list = [DataSet(**permission_value).value]
                    else:
                        raise ValueError(f"permission type {permission_type} is not supported")
                    for value in value_list:
                        if not permission_parameters.is_delete:
                            self._grant(permission_type, value, permission_parameters.valid_period)
                        else:
                            self._delete(permission_type, value)
                else:
                    if not permission_parameters.is_delete:
                        self._grant_all(permission_type, permission_parameters.valid_period)
                    else:
                        self._delete(permission_type)

    @DB.connection_context()
    def _grant(self, permission_type, value, valid_period=None):
        permission_list = PermissionStorage.query(source_role=self.src_role, source_party_id=self.src_party_id,
                                                  type=permission_type, value=value)
        if permission_list:
            if valid_period:
                for permission in permission_list:
                    permission.f_expire_time = self.make_expire_time(valid_period)
                    permission.save()
        else:
            permission = PermissionStorage()
            permission.f_source_role = self.src_role
            permission.f_source_party_id = self.src_party_id
            permission.f_type = permission_type
            permission.f_value = value
            permission.f_expire_time = self.make_expire_time(valid_period)
            permission.save()

    @DB.connection_context()
    def _grant_all(self, permission_type, valid_period=None):
        for value in self.all_value(permission_type):
            self._grant(permission_type, value, valid_period)

    @DB.connection_context()
    def query(self, **kwargs):
        logger.info(f"query {self.src_role} {self.src_party_id} {kwargs}")
        permission_list = PermissionStorage.query(
            source_role=self.src_role,
            source_party_id=self.src_party_id,
            **kwargs
        )
        _result = {}
        for permission in permission_list:
            if permission.f_type not in _result:
                _result[permission.f_type] = [[permission.f_value, permission.f_expire_time]]
            else:
                _result[permission.f_type].append([permission.f_value, permission.f_expire_time])
        logger.info(f"{_result}")
        return _result

    @DB.connection_context()
    def _delete(self, permission_type, value=None):
        update_filters = [
            PermissionStorage.f_source_role == self.src_role,
            PermissionStorage.f_source_party_id == self.src_party_id,
            PermissionStorage.f_type == permission_type
        ]
        if value:
            update_filters.append(PermissionStorage.f_value == value)
        rows = PermissionStorage.delete().where(*update_filters).execute()
        return rows

    def check_parameters(self, permission_parameters):
        for permission_type in PermissionType.values():
            permission_value = getattr(permission_parameters, permission_type)
            if permission_value:
                if permission_type == PermissionType.ROLE.value and not ROLE_PERMISSION:
                    raise ValueError(f"role permission switch is {ROLE_PERMISSION}")
                if permission_type == PermissionType.COMMAND.value and not COMPONENT_PERMISSION:
                    raise ValueError(f"component permission switch is {COMPONENT_PERMISSION}")
                if permission_type == PermissionType.DATASET.value and not DATASET_PERMISSION:
                    raise ValueError(f"dataset permission switch is {DATASET_PERMISSION}")
                if permission_type in [PermissionType.ROLE.value, PermissionType.COMMAND.value, PermissionType.COMPONENT.value]:
                    if permission_value != "*":
                        value_list = [value.strip() for value in permission_value.split(self.value_delimiter)]
                        self.check_values(permission_type, value_list)
                if permission_type in [PermissionType.DATASET.value]:
                    if isinstance(permission_value, list):
                        for dataset in permission_value:
                            DataSet(**dataset).check()
                    elif isinstance(permission_value, dict):
                        DataSet(**permission_value).check()
                    else:
                        raise ValueError(f"permission type {permission_type} value {permission_value} error")

    def check_values(self, permission_type, values):
        error_value = []
        value_list = self.all_value(permission_type)
        for value in values:
            if value not in value_list:
                error_value.append(value)
        if error_value:
            raise ValueError(f"permission type {permission_type} value {error_value} error")

    @classmethod
    def make_expire_time(cls, valid_period):
        if valid_period:
            return int(time.time()) + valid_period
        else:
            return None

    def all_value(self, permission_type):
        if permission_type == PermissionType.ROLE.value:
            value_list = self.all_role
        elif permission_type == PermissionType.COMMAND.value:
            value_list = self.all_command
        elif permission_type == PermissionType.COMPONENT.value:
            value_list = self.all_component
        else:
            raise Exception(f"permission type {permission_type} not support grant all")
        return value_list

    @property
    def all_role(self):
        return ["guest", "host", "arbiter"]

    @property
    def all_component(self):
        from fate_flow.db.db_models import ComponentInfo
        component_list = []
        for component in ComponentInfo.select():
            component_list.append(component.f_component_name.lower())
        return component_list

    @property
    def all_command(self):
        return ["create", "stop"]

    @property
    def value_delimiter(self):
        return ","


class PermissionCheck(object):
    def __init__(self, src_role, src_party_id, initiator, roles, role, party_id, component_list, dataset_list):
        self.src_role = src_role
        self.src_party_id = src_party_id
        self.role = role
        self.party_id = party_id
        self.component_list = component_list
        self.dataset_list = dataset_list
        self.initiator = initiator
        self.roles = roles
        self.controller = PermissionController(src_role, src_party_id)

    def check_role(self) -> PermissionReturn:
        if not self.controller.check(PermissionType.ROLE.value, self.role):
            return PermissionReturn(CheckReturn.NO_ROLE_PERMISSION, f"check role permission failed: {self.role}")

    def check_component(self) -> PermissionReturn:
        for component_name in self.component_list:
            if not self.controller.check(PermissionType.COMPONENT.value, component_name):
                return PermissionReturn(CheckReturn.NO_COMPONENT_PERMISSION, f"check component permission failed: {component_name}")

    def check_dataset(self) -> PermissionReturn:
        for dataset in self.dataset_list:
            if not self.controller.check(PermissionType.DATASET.value, dataset):
                return PermissionReturn(CheckReturn.NO_DATASET_PERMISSION, f"check dataset permission failed: {dataset}")