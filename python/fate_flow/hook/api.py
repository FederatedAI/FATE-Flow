import requests

from fate_flow.db.service_registry import ServiceRegistry
from fate_flow.entity.types import RegistryServiceName
from fate_flow.hook import HookManager
from fate_flow.hook.common.parameters import SignatureParameters, AuthenticationParameters, PermissionCheckParameters, \
    AuthenticationReturn, SignatureReturn, PermissionReturn, ClientAuthenticationParameters, ClientAuthenticationReturn
from fate_flow.settings import HOOK_SERVER_NAME


@HookManager.register_client_authentication_hook
def client_authentication(parm: ClientAuthenticationParameters) -> ClientAuthenticationReturn:
    service_list = ServiceRegistry.load_service(
        server_name=HOOK_SERVER_NAME,
        service_name=RegistryServiceName.CLIENT_AUTHENTICATION
    )
    if not service_list:
        raise Exception(f"client authentication error: no found server"
                        f" {HOOK_SERVER_NAME} service client_authentication")
    service = service_list[0]
    response = getattr(requests, service.f_method.lower(), None)(
        url=service.f_url,
        json=parm.to_dict()
    )
    if response.status_code != 200:
        raise Exception(
            f"client authentication error: request authentication url failed, status code {response.status_code}")
    elif response.json().get("code") != 0:
        return ClientAuthenticationReturn(code=response.json().get("code"), message=response.json().get("msg"))
    return ClientAuthenticationReturn()


@HookManager.register_site_signature_hook
def site_signature(parm: SignatureParameters) -> SignatureReturn:
    service_list = ServiceRegistry.load_service(server_name=HOOK_SERVER_NAME, service_name=RegistryServiceName.SIGNATURE)
    if not service_list:
        raise Exception(f"signature error: no found server {HOOK_SERVER_NAME} service signature")
    service = service_list[0]
    response = getattr(requests, service.f_method.lower(), None)(
        url=service.f_url,
        json=parm.to_dict()
    )
    if response.status_code == 200:
        if response.json().get("code") == 0:
            return SignatureReturn(signature=response.json().get("data"))
        else:
            raise Exception(f"signature error: request signature url failed, result: {response.json()}")
    else:
        raise Exception(f"signature error: request signature url failed, status code {response.status_code}")


@HookManager.register_site_authentication_hook
def site_authentication(parm: AuthenticationParameters) -> AuthenticationReturn:
    service_list = ServiceRegistry.load_service(server_name=HOOK_SERVER_NAME,
                                                service_name=RegistryServiceName.SITE_AUTHENTICATION)
    if not service_list:
        raise Exception(
            f"site authentication error: no found server {HOOK_SERVER_NAME} service site_authentication")
    service = service_list[0]
    response = getattr(requests, service.f_method.lower(), None)(
        url=service.f_url,
        json=parm.to_dict()
    )
    if response.status_code != 200:
        raise Exception(
            f"site authentication error: request site_authentication url failed, status code {response.status_code}")
    elif response.json().get("code") != 0:
        return AuthenticationReturn(code=response.json().get("code"), message=response.json().get("msg"))
    return AuthenticationReturn()


@HookManager.register_permission_check_hook
def permission_check(parm: PermissionCheckParameters) -> PermissionReturn:
    service_list = ServiceRegistry.load_service(server_name=HOOK_SERVER_NAME, service_name=RegistryServiceName.PERMISSION_CHECK)
    if not service_list:
        raise Exception(f"permission check error: no found server {HOOK_SERVER_NAME} service permission")
    service = service_list[0]
    response = getattr(requests, service.f_method.lower(), None)(
        url=service.f_url,
        json=parm.to_dict()
    )
    if response.status_code != 200:
        raise Exception(
            f"permission check error: request permission url failed, status code {response.status_code}")
    elif response.json().get("code") != 0:
        return PermissionReturn(code=response.json().get("code"), message=response.json().get("msg"))
    return PermissionReturn()
