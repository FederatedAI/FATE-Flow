from fate_flow.controller.app_controller import Authentication, PermissionController
from fate_flow.entity.code import ReturnCode
from fate_flow.errors.job import InvalidParameter
from fate_flow.hook import HookManager
from fate_flow.hook.common.parameters import AuthenticationReturn, AuthenticationParameters


@HookManager.register_client_authentication_hook
def authentication(parm: AuthenticationParameters) -> AuthenticationReturn:
    app_id = parm.headers.get("app_id")
    user_name = parm.headers.get("user_name")
    timestamp = parm.headers.get("timestamp")
    nonce = parm.headers.get("nonce")
    signature = parm.headers.get("signature")
    check_parameters(app_id, user_name, timestamp, nonce, signature)
    if Authentication.md5_verify(app_id, timestamp, nonce, signature, user_name):
        if PermissionController.enforcer(app_id, parm.path, parm.method):
            return AuthenticationReturn(code=ReturnCode.Base.SUCCESS, message="success")
        else:
            return AuthenticationReturn(code=ReturnCode.API.AUTHENTICATION_FAILED,
                                        message="Authentication Failed")
    else:
        return AuthenticationReturn(code=ReturnCode.API.VERIFY_FAILED, message="varify failed!")


def check_parameters(app_id, user_name, time_stamp, nonce, signature):
    if not app_id:
        raise InvalidParameter(name="app-id")
    if not time_stamp or not isinstance(time_stamp, str):
        raise InvalidParameter(name="timestamp")
    if not nonce or not isinstance(time_stamp, str) or len(nonce) != 4:
        raise InvalidParameter(name="nonce")
    if not signature:
        raise InvalidParameter(name="signature")
