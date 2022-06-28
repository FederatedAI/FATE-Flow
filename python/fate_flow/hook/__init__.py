import importlib

from fate_flow.hook.common.parameters import SignatureParameters, AuthenticationParameters, PermissionCheckParameters, \
    SignatureReturn, AuthenticationReturn, PermissionReturn, ClientAuthenticationReturn, ClientAuthenticationParameters
from fate_flow.settings import HOOK_MODULE


class HookManager:
    SITE_SIGNATURE = None
    SITE_AUTHENTICATION = None
    CLIENT_AUTHENTICATION = None
    PERMISSION_CHECK = None

    @staticmethod
    def init():
        importlib.import_module(HOOK_MODULE)

    @staticmethod
    def register_site_signature_hook(func):
        HookManager.SITE_SIGNATURE = func

    @staticmethod
    def register_site_authentication_hook(func):
        HookManager.SITE_AUTHENTICATION = func

    @staticmethod
    def register_client_authentication_hook(func):
        HookManager.CLIENT_AUTHENTICATION = func

    @staticmethod
    def register_permission_check_hook(func):
        HookManager.PERMISSION_CHECK = func

    @staticmethod
    def client_authentication(parm: ClientAuthenticationParameters) -> ClientAuthenticationReturn:
        if HookManager.CLIENT_AUTHENTICATION is not None:
            return HookManager.CLIENT_AUTHENTICATION(parm)
        return ClientAuthenticationReturn()

    @staticmethod
    def site_signature(parm: SignatureParameters) -> SignatureReturn:
        if HookManager.SITE_SIGNATURE is not None:
            return HookManager.SITE_SIGNATURE(parm)
        return SignatureReturn()

    @staticmethod
    def site_authentication(parm: AuthenticationParameters) -> AuthenticationReturn:
        if HookManager.SITE_AUTHENTICATION is not None:
            return HookManager.SITE_AUTHENTICATION(parm)
        return AuthenticationReturn()

    @staticmethod
    def permission_check(parm: PermissionCheckParameters) -> PermissionReturn:
        if HookManager.PERMISSION_CHECK is not None:
            return HookManager.PERMISSION_CHECK(parm)
        return PermissionReturn()
