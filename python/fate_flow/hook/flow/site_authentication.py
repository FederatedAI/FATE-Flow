import hashlib

from fate_flow.controller.permission import PermissionController, Authentication
from fate_flow.entity.code import ReturnCode
from fate_flow.errors.server_error import NoFoundAppid
from fate_flow.hook import HookManager
from fate_flow.hook.common.parameters import SignatureParameters, SignatureReturn, AuthenticationParameters, \
    AuthenticationReturn
from fate_flow.manager.service.app_manager import AppManager
from fate_flow.runtime.system_settings import LOCAL_PARTY_ID, PARTY_ID


@HookManager.register_site_signature_hook
def signature(parm: SignatureParameters) -> SignatureReturn:
    if parm.party_id == LOCAL_PARTY_ID:
        parm.party_id = PARTY_ID
    apps = AppManager.query_partner_app(party_id=parm.party_id)
    if not apps:
        e = NoFoundAppid(party_id=parm.party_id)
        return SignatureReturn(
            code=e.code,
            message=e.message
        )
    app = apps[0]
    nonce = Authentication.generate_nonce()
    timestamp = Authentication.generate_timestamp()
    initiator_party_id = parm.initiator_party_id if parm.initiator_party_id else ""
    key = hashlib.md5(str(app.f_app_id + initiator_party_id + nonce + timestamp).encode("utf8")).hexdigest().lower()
    sign = hashlib.md5(str(key + app.f_app_token).encode("utf8")).hexdigest().lower()

    return SignatureReturn(signature={
        "Signature": sign,
        "appId": app.f_app_id,
        "Nonce": nonce,
        "Timestamp": timestamp,
        "initiatorPartyId": initiator_party_id
    })


@HookManager.register_site_authentication_hook
def authentication(parm: AuthenticationParameters) -> AuthenticationReturn:
    app_id = parm.headers.get("appId")
    timestamp = parm.headers.get("Timestamp")
    nonce = parm.headers.get("Nonce")
    sign = parm.headers.get("Signature")
    initiator_party_id = parm.headers.get("initiatorPartyId")
    check_parameters(app_id, timestamp, nonce, sign)
    if Authentication.md5_verify(app_id, timestamp, nonce, sign, initiator_party_id):
        if PermissionController.enforcer(app_id, parm.path, parm.method):
            return AuthenticationReturn(code=ReturnCode.Base.SUCCESS, message="success")
        else:
            return AuthenticationReturn(code=ReturnCode.API.AUTHENTICATION_FAILED,
                                        message=f"Authentication Failed: app_id[{app_id}, path[{parm.path}, method[{parm.method}]]]")
    else:
        return AuthenticationReturn(code=ReturnCode.API.VERIFY_FAILED, message="varify failed!")


def check_parameters(app_id, time_stamp, nonce, sign):
    if not app_id:
        raise ValueError(ReturnCode.API.INVALID_PARAMETER, "invalid parameter: appId")
    if not time_stamp or not isinstance(time_stamp, str):
        raise ValueError(ReturnCode.API.INVALID_PARAMETER, "invalid parameter:timeStamp")
    if not nonce or not isinstance(time_stamp, str) or len(nonce) != 4:
        raise ValueError(ReturnCode.API.INVALID_PARAMETER, "invalid parameter: Nonce")
    if not sign:
        raise ValueError(ReturnCode.API.INVALID_PARAMETER, "invalid parameter: Signature")
