import requests

from fate_flow.controller.permission_controller import PermissionCheck
from fate_flow.hook.manager import HookManager
from fate_flow.hook.parameters import SignatureParameters, AuthenticationParameters, PermissionCheckParameters, \
    AuthenticationReturn, SignatureReturn, PermissionReturn, StatusCode
from fate_flow.settings import ROLE_PERMISSION, COMPONENT_PERMISSION, DATASET_PERMISSION, AUTHENTICATION


@HookManager.register_signature_hook
def signature(parm: SignatureParameters):
    sign = None
    return SignatureReturn(sign)


@HookManager.register_authentication_hook
def authentication(parm: AuthenticationParameters):
    return AuthenticationReturn()


@HookManager.register_permission_check_hook
def permission_check(parm: PermissionCheckParameters) -> PermissionReturn:
    checker = PermissionCheck(**parm.to_dict())
    if ROLE_PERMISSION:
        role_result = checker.check_role()
        if role_result.code != StatusCode.SUCCESS:
            return role_result

    if COMPONENT_PERMISSION:
        component_result = checker.check_component()
        if component_result.code != StatusCode.SUCCESS:
            return component_result

    if DATASET_PERMISSION:
        dataset_result = checker.check_dataset()
        if dataset_result.code != StatusCode.SUCCESS:
            return dataset_result

    return PermissionReturn()


