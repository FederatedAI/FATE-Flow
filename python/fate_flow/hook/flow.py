import requests

from fate_flow.controller.permission_controller import PermissionCheck
from fate_flow.db.service_registry import ServiceRegistry
from fate_flow.entity import RetCode
from fate_flow.hook.manager import HookManager
from fate_flow.hook.parameters import SignatureParameters, AuthenticationParameters, PermissionCheckParameters, \
    AuthenticationReturn, SignatureReturn, PermissionReturn
from fate_flow.settings import ROLE_PERMISSION, COMPONENT_PERMISSION, DATASET_PERMISSION, SITE_AUTHENTICATION_SERVER


@HookManager.register_site_signature_hook
def site_signature(parm: SignatureParameters):
    service_list = ServiceRegistry.load_service(server_name=SITE_AUTHENTICATION_SERVER, service_name="signature")
    if not service_list:
        raise Exception(f"signature error: no found server {SITE_AUTHENTICATION_SERVER} service signature")
    service = service_list[0]
    json_body = service.f_data
    response = getattr(requests, service.f_method.lower(), None)(
        url=service.f_url,
        json=json_body
    )
    if response.status_code == 200:
        sign = response.json().get("data")
        sign["srcPartyId"] = parm.party_id
        return SignatureReturn(sign)
    else:
        raise Exception(f"signature error: request signature url failed, status code {response.status_code}")


@HookManager.register_site_authentication_hook
def site_authentication(parm: AuthenticationParameters):
    service_list = ServiceRegistry.load_service(server_name=SITE_AUTHENTICATION_SERVER, service_name="authentication")
    if not service_list:
        raise Exception(f"authentication error: no found server {SITE_AUTHENTICATION_SERVER} service authentication")
    service = service_list[0]
    json_body = service.f_data
    json_body.update(parm.sign)
    response = getattr(requests, service.f_method.lower(), None)(
        url=service.f_url,
        json=json_body
    )
    if response.status_code != 200:
        raise Exception(
            f"authentication error: request authentication url failed, status code {response.status_code}")
    elif response.json().get("code") != 0:
        return AuthenticationReturn(code=response.json().get("code"), message=response.json().get("msg"))
    return AuthenticationReturn()


@HookManager.register_permission_check_hook
def permission_check(parm: PermissionCheckParameters) -> PermissionReturn:
    if parm.role == "local" or str(parm.party_id) == "0":
        return PermissionReturn()

    if parm.src_party_id == parm.party_id:
        return PermissionReturn()

    checker = PermissionCheck(**parm.to_dict())
    if ROLE_PERMISSION:
        role_result = checker.check_role()
        if role_result.code != RetCode.SUCCESS:
            return role_result

    if COMPONENT_PERMISSION:
        component_result = checker.check_component()
        if component_result.code != RetCode.SUCCESS:
            return component_result

    if DATASET_PERMISSION:
        dataset_result = checker.check_dataset()
        if dataset_result.code != RetCode.SUCCESS:
            return dataset_result
    return PermissionReturn()


@HookManager.register_client_authentication_hook
def client_authentication() -> AuthenticationReturn:
    from base64 import b64encode
    from hmac import HMAC
    from time import time
    from urllib.parse import quote, urlencode

    from flask import request

    from fate_flow.settings import HTTP_APP_KEY, HTTP_SECRET_KEY, MAX_TIMESTAMP_INTERVAL

    if not (HTTP_APP_KEY and HTTP_SECRET_KEY):
        return AuthenticationReturn(code=RetCode.AUTHENTICATION_ERROR, message=f"settings HTTP_APP_KEY and HTTP_SECRET_KEY is None")

    requirement_parm = ['TIMESTAMP', 'NONCE', 'APP_KEY', 'SIGNATURE']
    for parm in requirement_parm:
        if not request.headers.get(parm):
            return AuthenticationReturn(code=RetCode.AUTHENTICATION_ERROR, message=f"requirement headers parameters: {requirement_parm}")
    try:
        timestamp = int(request.headers['TIMESTAMP']) / 1000
    except Exception:
        return AuthenticationReturn(code=RetCode.AUTHENTICATION_ERROR, message="Invalid TIMESTAMP")

    now = time()
    if not now - MAX_TIMESTAMP_INTERVAL < timestamp < now + MAX_TIMESTAMP_INTERVAL:
        return AuthenticationReturn(
            code=RetCode.AUTHENTICATION_ERROR,
            message=f'TIMESTAMP is more than {MAX_TIMESTAMP_INTERVAL} seconds away from the server time'
        )

    if not request.headers['NONCE']:
        return AuthenticationReturn(
            code=RetCode.AUTHENTICATION_ERROR,
            message='Invalid NONCE'
        )

    if request.headers['APP_KEY'] != HTTP_APP_KEY:
        return AuthenticationReturn(
            code=RetCode.AUTHENTICATION_ERROR,
            message='Unknown APP_KEY'
        )

    # authentication
    signature = b64encode(HMAC(HTTP_SECRET_KEY.encode('ascii'), b'\n'.join([
        request.headers['TIMESTAMP'].encode('ascii'),
        request.headers['NONCE'].encode('ascii'),
        request.headers['APP_KEY'].encode('ascii'),
        request.full_path.rstrip('?').encode('ascii'),
        request.data if request.json else b'',
        # quote_via: `urllib.parse.quote` replaces spaces with `%20`
        # safe: unreserved characters from rfc3986
        urlencode(sorted(request.form.items()), quote_via=quote, safe='-._~').encode('ascii')
        if request.form else b'',
    ]), 'sha1').digest()).decode('ascii')
    if signature != request.headers['SIGNATURE']:
        return AuthenticationReturn(
            code=RetCode.AUTHENTICATION_ERROR,
            message='signature authentication failed'
        )

    return AuthenticationReturn()
