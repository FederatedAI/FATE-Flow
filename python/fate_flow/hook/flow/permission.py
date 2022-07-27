from fate_flow.controller.permission_controller import PermissionCheck
from fate_flow.entity import RetCode
from fate_flow.hook import HookManager
from fate_flow.hook.common.parameters import PermissionCheckParameters, PermissionReturn
from fate_flow.settings import COMPONENT_PERMISSION, DATASET_PERMISSION


@HookManager.register_permission_check_hook
def permission(parm: PermissionCheckParameters) -> PermissionReturn:
    if parm.role == "local" or str(parm.party_id) == "0":
        return PermissionReturn()

    if parm.src_party_id == parm.party_id:
        return PermissionReturn()

    checker = PermissionCheck(**parm.to_dict())

    if COMPONENT_PERMISSION:
        component_result = checker.check_component()
        if component_result.code != RetCode.SUCCESS:
            return component_result

    if DATASET_PERMISSION:
        dataset_result = checker.check_dataset()
        if dataset_result.code != RetCode.SUCCESS:
            return dataset_result
    return PermissionReturn()
