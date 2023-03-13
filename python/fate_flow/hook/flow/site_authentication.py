import hashlib

from fate_flow.controller.app_controller import PermissionController, Authentication
from fate_flow.entity.code import ReturnCode
from fate_flow.entity.types import AppType
from fate_flow.hook import HookManager
from fate_flow.hook.common.parameters import SignatureParameters, SignatureReturn, AuthenticationParameters, \
    AuthenticationReturn
from fate_flow.manager.app_manager import AppManager
from fate_flow.runtime.system_settings import LOCAL_PARTY_ID, PARTY_ID


@HookManager.register_site_signature_hook
def signature(parm: SignatureParameters) -> SignatureReturn:
    if parm.party_id == LOCAL_PARTY_ID:
        parm.party_id = PARTY_ID
    apps = AppManager.query_partner_app(party_id=parm.party_id)
    if not apps:
        return SignatureReturn(
            code=ReturnCode.API.NO_FOUND_APPID,
            message="Signature Failed"
        )
    app = apps[0]
    nonce = Authentication.generate_nonce()
    timestamp = Authentication.generate_timestamp()
    key = hashlib.md5(str(app.f_app_id + nonce + timestamp).encode("utf8")).hexdigest().lower()
    sign = hashlib.md5(str(key + app.f_app_token).encode("utf8")).hexdigest().lower()

    return SignatureReturn(signature={
        "signature": sign,
        "app_id": app.f_app_id,
        "nonce": nonce,
        "timestamp": timestamp
    })


@HookManager.register_site_authentication_hook
def authentication(parm: AuthenticationParameters) -> AuthenticationReturn:
    app_id = parm.headers.get("app_id")
    timestamp = parm.headers.get("timestamp")
    nonce = parm.headers.get("nonce")
    sign = parm.headers.get("signature")
    check_parameters(app_id, timestamp, nonce, sign)
    if Authentication.md5_verify(app_id, timestamp, nonce, sign):
        if PermissionController.enforcer(app_id, parm.path, parm.method):
            return AuthenticationReturn(code=ReturnCode.Base.SUCCESS, message="success")
        else:
            return AuthenticationReturn(code=ReturnCode.API.AUTHENTICATION_FAILED,
                                        message="Authentication Failed")
    else:
        return AuthenticationReturn(code=ReturnCode.API.VERIFY_FAILED, message="varify failed!")


def check_parameters(app_id, time_stamp, nonce, sign):
    if not app_id:
        raise ValueError(ReturnCode.API.INVALID_PARAMETER, "invalid parameter: app-id")
    if not time_stamp or not isinstance(time_stamp, str):
        raise ValueError(ReturnCode.API.INVALID_PARAMETER, "invalid parameter:timestamp")
    if not nonce or not isinstance(time_stamp, str) or len(nonce) != 4:
        raise ValueError(ReturnCode.API.INVALID_PARAMETER, "invalid parameter: nonce")
    if not sign:
        raise ValueError(ReturnCode.API.INVALID_PARAMETER, "invalid parameter: signature")
