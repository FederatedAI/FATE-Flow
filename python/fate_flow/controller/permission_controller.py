from fate_flow.db.fate_casbin import CB
from fate_flow.utils.log_utils import getLogger
from fate_flow.entity.permission_parameters import PermissionParameters, DataSet, CheckReturn
from fate_flow.entity.types import PermissionType
from fate_flow.hook.common.parameters import PermissionReturn
from fate_flow.settings import DATASET_PERMISSION, COMPONENT_PERMISSION, CASBIN_MODEL_CONF

logger = getLogger("permission")


class PermissionController:
    def __init__(self, src_party_id):
        self.src_party_id = str(src_party_id)
        self.casbin_controller = CB
        if not self.casbin_controller:
            raise Exception("No permission controller is found, please check whether the switch of permission control"
                            " is turned on")

    def check(self, permission_type, value):
        logger.info(f"check source party id {self.src_party_id} {permission_type} {value}")
        result = self.casbin_controller.enforce(self.src_party_id, permission_type, value)
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
                        raise ValueError(f"permission type {permission_type} is not supported")
                    for value in value_list:
                        if not permission_parameters.is_delete:
                            self.casbin_controller.grant(self.src_party_id, permission_type, value)
                        else:
                            self.casbin_controller.delete(self.src_party_id, permission_type, value)
                else:
                    if not permission_parameters.is_delete:
                        for value in self.all_value(permission_type):
                            self.casbin_controller.grant(self.src_party_id, permission_type, value)
                    else:
                        self.casbin_controller.delete_all(self.src_party_id, permission_type)

    def query(self):
        result = {PermissionType.DATASET.value: [], PermissionType.COMPONENT.value: []}
        for casbin_result in self.casbin_controller.query(self.src_party_id):
            if casbin_result[1] == PermissionType.DATASET.value:
                casbin_result[2] = DataSet.load_casbin_value(casbin_result[2])
            result[casbin_result[1]].append(casbin_result[2])
        return result

    def check_parameters(self, permission_parameters):
        for permission_type in PermissionType.values():
            permission_value = getattr(permission_parameters, permission_type)
            if permission_value:
                if permission_type == PermissionType.COMPONENT.value and not COMPONENT_PERMISSION:
                    raise ValueError(f"component permission switch is {COMPONENT_PERMISSION}")
                if permission_type == PermissionType.DATASET.value and not DATASET_PERMISSION:
                    raise ValueError(f"dataset permission switch is {DATASET_PERMISSION}")
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
                        raise ValueError(f"permission type {permission_type} value {permission_value} error")

    def check_values(self, permission_type, values):
        error_value = []
        value_list = self.all_value(permission_type)
        for value in values:
            if value not in value_list:
                error_value.append(value)
        if error_value:
            raise ValueError(f"permission type {permission_type} value {error_value} error")

    def all_value(self, permission_type):
        if permission_type == PermissionType.COMPONENT.value:
            value_list = self.all_component
        else:
            raise Exception(f"permission type {permission_type} not support grant all")
        return value_list

    @property
    def all_component(self):
        from fate_flow.db.db_models import ComponentInfo
        component_list = []
        for component in ComponentInfo.select():
            component_list.append(component.f_component_name.lower())
        return component_list

    @property
    def value_delimiter(self):
        return ","


class PermissionCheck(object):
    def __init__(self, src_party_id, component_list, dataset_list, **kwargs):
        self.component_list = component_list
        self.dataset_list = dataset_list
        self.controller = PermissionController(src_party_id)

    def check_component(self) -> PermissionReturn:
        for component_name in self.component_list:
            if not self.controller.check(PermissionType.COMPONENT.value, component_name):
                return PermissionReturn(CheckReturn.NO_COMPONENT_PERMISSION, f"check component permission failed: {component_name}")
        return PermissionReturn()

    def check_dataset(self) -> PermissionReturn:
        for dataset in self.dataset_list:
            if not self.controller.check(PermissionType.DATASET.value, dataset.casbin_value):
                return PermissionReturn(CheckReturn.NO_DATASET_PERMISSION, f"check dataset permission failed: {dataset.value}")
        return PermissionReturn()