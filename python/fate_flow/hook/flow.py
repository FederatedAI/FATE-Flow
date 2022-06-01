import requests

from fate_flow.controller.permission_controller import PermissionCheck
from fate_flow.db.service_registry import ServiceRegistry
from fate_flow.hook.manager import HookManager
from fate_flow.hook.parameters import SignatureParameters, AuthenticationParameters, PermissionCheckParameters, \
    AuthenticationReturn, SignatureReturn, PermissionReturn, StatusCode
from fate_flow.settings import ROLE_PERMISSION, COMPONENT_PERMISSION, DATASET_PERMISSION, AUTHENTICATION_SERVER, AUTHENTICATION


@HookManager.register_signature_hook
def signature(parm: SignatureParameters):
    sign = None
    if AUTHENTICATION:
        service_list = ServiceRegistry.load_service(server_name=AUTHENTICATION_SERVER, service_name="signature")
        if not service_list:
            raise Exception(f"signature error: no found server {AUTHENTICATION_SERVER} service {signature}")
        service = service_list[0]
        json_body = service.f_data
        response = getattr(requests, service.f_method.lower(), None)(
            url=service.f_url,
            json=json_body
        )
        if response.status_code == 200:
            sign = response.json().get("data")
            sign["srcPartyId"] = parm.party_id
        else:
            raise Exception(f"signature error: request signature url failed, status code {response.status_code}")
    return SignatureReturn(sign)


@HookManager.register_authentication_hook
def authentication(parm: AuthenticationParameters):
    result = AuthenticationReturn()
    if AUTHENTICATION:
        service_list = ServiceRegistry.load_service(server_name=AUTHENTICATION_SERVER, service_name="authentication")
        if not service_list:
            raise Exception(f"authentication error: no found server {AUTHENTICATION_SERVER} service {signature}")
        service = service_list[0]
        json_body = service.f_data
        json_body.update(parm.sign)
        response = getattr(requests, service.f_method.lower(), None)(
            url=service.f_url,
            json=json_body
        )
        if response.status_code != 200:
            raise Exception(f"authentication error: request authentication url failed, status code {response.status_code}")
        elif response.json().get("code") != 0:
            return AuthenticationReturn(code=response.json().get("code"), message=response.json().get("msg"))
    return result


@HookManager.register_permission_check_hook
def permission_check(parm: PermissionCheckParameters) -> PermissionReturn:
    if check_pass(parm):
        return PermissionReturn()

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


def check_pass(parm: PermissionCheckParameters):
    if parm.role == "local" or str(parm.party_id) == "0":
        return True
    elif parm.src_party_id == parm.party_id:
        return True
    else:
        return False
