import requests

from fate_flow.db.service_registry import ServiceRegistry
from fate_flow.entity.types import RegistryServiceName
from fate_flow.hook import HookManager
from fate_flow.hook.common.parameters import ClientAuthenticationParameters, ClientAuthenticationReturn
from fate_flow.settings import HOOK_SERVER_NAME


@HookManager.register_client_authentication_hook
def authentication(parm: ClientAuthenticationParameters) -> ClientAuthenticationReturn:
    service_list = ServiceRegistry().load_api_info(service_name=HOOK_SERVER_NAME,
                                                   url_name=RegistryServiceName.CLIENT_AUTHENTICATION.value)
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