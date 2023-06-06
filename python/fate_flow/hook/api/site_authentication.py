import requests

from fate_flow.db.service_registry import ServiceRegistry
from fate_flow.entity.types import RegistryServiceName
from fate_flow.hook import HookManager
from fate_flow.hook.common.parameters import SignatureParameters, AuthenticationParameters, AuthenticationReturn,\
    SignatureReturn
from fate_flow.settings import HOOK_SERVER_NAME, PARTY_ID


@HookManager.register_site_signature_hook
def signature(parm: SignatureParameters) -> SignatureReturn:
    service_list = ServiceRegistry.load_service(server_name=HOOK_SERVER_NAME, service_name=RegistryServiceName.SIGNATURE.value)
    if not service_list:
        raise Exception(f"signature error: no found server {HOOK_SERVER_NAME} service signature")
    service = service_list[0]
    data = service.f_data if service.f_data else {}
    data.update(parm.to_dict())
    response = getattr(requests, service.f_method.lower(), None)(
        url=service.f_url,
        json=data
    )
    if response.status_code == 200:
        if response.json().get("code") == 0:
            return SignatureReturn(site_signature=response.json().get("data"))
        else:
            raise Exception(f"signature error: request signature url failed, result: {response.json()}")
    else:
        raise Exception(f"signature error: request signature url failed, status code {response.status_code}")


@HookManager.register_site_authentication_hook
def authentication(parm: AuthenticationParameters) -> AuthenticationReturn:
    if not parm.src_party_id or str(parm.src_party_id) == "0":
        parm.src_party_id = PARTY_ID
    service_list = ServiceRegistry.load_service(server_name=HOOK_SERVER_NAME,
                                                service_name=RegistryServiceName.SITE_AUTHENTICATION.value)
    if not service_list:
        raise Exception(
            f"site authentication error: no found server {HOOK_SERVER_NAME} service site_authentication")
    service = service_list[0]
    data = service.f_data if service.f_data else {}
    data.update(parm.to_dict())
    response = getattr(requests, service.f_method.lower(), None)(
        url=service.f_url,
        json=data
    )
    if response.status_code != 200:
        raise Exception(
            f"site authentication error: request site_authentication url failed, status code {response.status_code}")
    elif response.json().get("code") != 0:
        return AuthenticationReturn(code=response.json().get("code"), message=response.json().get("msg"))
    return AuthenticationReturn()