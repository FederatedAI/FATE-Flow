from fate_flow.hook import HookManager
from fate_flow.hook.common.parameters import PermissionCheckParameters, PermissionReturn


@HookManager.register_permission_check_hook
def permission(parm: PermissionCheckParameters) -> PermissionReturn:
    return PermissionReturn()
