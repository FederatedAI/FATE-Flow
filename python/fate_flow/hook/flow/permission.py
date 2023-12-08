from fate_flow.controller.permission import PermissionCheck
from fate_flow.entity.code import ReturnCode
from fate_flow.hook import HookManager
from fate_flow.hook.common.parameters import PermissionCheckParameters, PermissionReturn
from fate_flow.runtime.system_settings import LOCAL_PARTY_ID, PARTY_ID


@HookManager.register_permission_check_hook
def permission(parm: PermissionCheckParameters) -> PermissionReturn:
    if parm.party_id == LOCAL_PARTY_ID or parm.party_id == PARTY_ID:
        return PermissionReturn()

    checker = PermissionCheck(**parm.to_dict())
    component_result = checker.check_component()

    if component_result.code != ReturnCode.Base.SUCCESS:
        return component_result

    dataset_result = checker.check_dataset()
    if dataset_result.code != ReturnCode.Base.SUCCESS:
        return dataset_result
    return PermissionReturn()
