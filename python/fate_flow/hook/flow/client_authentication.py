from fate_flow.controller.app_controller import Authentication, PermissionController
from fate_flow.entity.code import ReturnCode
from fate_flow.hook import HookManager
from fate_flow.hook.common.parameters import ClientAuthenticationReturn, ClientAuthenticationParameters


@HookManager.register_client_authentication_hook
def authentication(parm: ClientAuthenticationParameters) -> ClientAuthenticationReturn:
    app_id = parm.headers.get("app_id")
    user_name = parm.headers.get("user_name")
    timestamp = parm.headers.get("timestamp")
    nonce = parm.headers.get("nonce")
    signature = parm.headers.get("signature")
    check_parameters(app_id, user_name, timestamp, nonce, signature)
    if Authentication.md5_verify(app_id, user_name, timestamp, nonce, signature):
        if PermissionController.enforcer(app_id, parm.path, parm.method):
            return ClientAuthenticationReturn(code=ReturnCode.Base.SUCCESS, message="success")
        else:
            return ClientAuthenticationReturn(code=ReturnCode.API.AUTHENTICATION_FAILED,
                                              message="Authentication Failed")
    else:
        return ClientAuthenticationReturn(code=ReturnCode.API.VERIFY_FAILED, message="varify failed!")


def check_parameters(app_id, user_name, time_stamp, nonce, signature):
    if not app_id:
        raise ValueError(ReturnCode.API.INVALID_PARAMETER, "invalid parameter: app-id")
    if not time_stamp or not isinstance(time_stamp, str):
        raise ValueError(ReturnCode.API.INVALID_PARAMETER, "invalid parameter:timestamp")
    if not nonce or not isinstance(time_stamp, str) or len(nonce) != 4:
        raise ValueError(ReturnCode.API.INVALID_PARAMETER, "invalid parameter: nonce")
    if not signature:
        raise ValueError(ReturnCode.API.INVALID_PARAMETER, "invalid parameter: signature")
