import base64
import json

from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import MD5

from fate_flow.controller.permission_controller import PermissionCheck
from fate_flow.db.key_manager import RsaKeyManager
from fate_flow.entity import RetCode
from fate_flow.entity.types import SiteKeyName
from fate_flow.hook import HookManager
from fate_flow.hook.common.parameters import SignatureParameters, AuthenticationParameters, PermissionCheckParameters, \
    AuthenticationReturn, SignatureReturn, PermissionReturn, ClientAuthenticationReturn, ClientAuthenticationParameters
from fate_flow.settings import COMPONENT_PERMISSION, DATASET_PERMISSION, PARTY_ID


@HookManager.register_client_authentication_hook
def client_authentication(parm: ClientAuthenticationParameters) -> ClientAuthenticationReturn:
    from base64 import b64encode
    from hmac import HMAC
    from time import time
    from urllib.parse import quote, urlencode

    from fate_flow.settings import HTTP_APP_KEY, HTTP_SECRET_KEY, MAX_TIMESTAMP_INTERVAL

    if not (HTTP_APP_KEY and HTTP_SECRET_KEY):
        return ClientAuthenticationReturn(code=RetCode.AUTHENTICATION_ERROR,
                                          message=f"settings HTTP_APP_KEY and HTTP_SECRET_KEY is None")

    requirement_parm = ['TIMESTAMP', 'NONCE', 'APP_KEY', 'SIGNATURE']
    for _p in requirement_parm:
        if not parm.headers.get(_p):
            return ClientAuthenticationReturn(code=RetCode.AUTHENTICATION_ERROR,
                                              message=f"requirement headers parameters: {requirement_parm}")
    try:
        timestamp = int(parm.headers['TIMESTAMP']) / 1000
    except Exception:
        return ClientAuthenticationReturn(code=RetCode.AUTHENTICATION_ERROR, message="Invalid TIMESTAMP")
    now = time()
    if not now - MAX_TIMESTAMP_INTERVAL < timestamp < now + MAX_TIMESTAMP_INTERVAL:
        return ClientAuthenticationReturn(
            code=RetCode.AUTHENTICATION_ERROR,
            message=f'TIMESTAMP is more than {MAX_TIMESTAMP_INTERVAL} seconds away from the server time'
        )

    if not parm.headers['NONCE']:
        return ClientAuthenticationReturn(
            code=RetCode.AUTHENTICATION_ERROR,
            message='Invalid NONCE'
        )

    if parm.headers['APP_KEY'] != HTTP_APP_KEY:
        return ClientAuthenticationReturn(
            code=RetCode.AUTHENTICATION_ERROR,
            message='Unknown APP_KEY'
        )

    # authentication
    signature = b64encode(HMAC(HTTP_SECRET_KEY.encode('ascii'), b'\n'.join([
        parm.headers['TIMESTAMP'].encode('ascii'),
        parm.headers['NONCE'].encode('ascii'),
        parm.headers['APP_KEY'].encode('ascii'),
        parm.full_path.rstrip('?').encode('ascii'),
        parm.data if parm.json else b'',
        # quote_via: `urllib.parse.quote` replaces spaces with `%20`
        # safe: unreserved characters from rfc3986
        urlencode(sorted(parm.form.items()), quote_via=quote, safe='-._~').encode('ascii')
        if parm.form else b'',
    ]), 'sha1').digest()).decode('ascii')
    if signature != parm.headers['SIGNATURE']:
        return ClientAuthenticationReturn(
            code=RetCode.AUTHENTICATION_ERROR,
            message='signature authentication failed'
        )
    return ClientAuthenticationReturn()


@HookManager.register_site_signature_hook
def site_signature(parm: SignatureParameters) -> SignatureReturn:
    private_key = RsaKeyManager.get_key(parm.party_id, key_name=SiteKeyName.PRIVATE.value)
    if not private_key:
        raise Exception(f"signature error: no found party id {parm.party_id} private key")
    signature = PKCS1_v1_5.new(RSA.importKey(private_key)).sign(MD5.new(json.dumps(parm.body).encode()))
    return SignatureReturn(base64.b64encode(signature).decode())


@HookManager.register_site_authentication_hook
def site_authentication(parm: AuthenticationParameters) -> AuthenticationReturn:
    party_id = parm.src_party_id if parm.src_party_id and str(parm.src_party_id) != "0" else PARTY_ID
    public_key = RsaKeyManager.get_key(party_id=party_id, key_name=SiteKeyName.PUBLIC.value)
    if not public_key:
        raise Exception(f"signature error: no found party id {party_id} public key")
    verifier = PKCS1_v1_5.new(RSA.importKey(public_key))
    if verifier.verify(MD5.new(json.dumps(parm.body).encode()), base64.b64decode(parm.sign)) is True:
        return AuthenticationReturn()
    else:
        return AuthenticationReturn(code=RetCode.AUTHENTICATION_ERROR, message="authentication failed")


@HookManager.register_permission_check_hook
def permission_check(parm: PermissionCheckParameters) -> PermissionReturn:
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
