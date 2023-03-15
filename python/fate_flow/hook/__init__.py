import importlib

from fate_flow.hook.common.parameters import SignatureParameters, AuthenticationParameters, PermissionCheckParameters, \
    SignatureReturn, AuthenticationReturn, PermissionReturn
from fate_flow.runtime.system_settings import HOOK_MODULE, stat_logger, CLIENT_AUTHENTICATION, SITE_AUTHENTICATION
from fate_flow.entity.code import ReturnCode


class HookManager:
    SITE_SIGNATURE = []
    SITE_AUTHENTICATION = []
    CLIENT_AUTHENTICATION = []
    PERMISSION_CHECK = []

    @staticmethod
    def init():
        if HOOK_MODULE is not None and (CLIENT_AUTHENTICATION or SITE_AUTHENTICATION):
            for modules in HOOK_MODULE.values():
                for module in modules.split(";"):
                    try:
                        importlib.import_module(module)
                    except Exception as e:
                        stat_logger.exception(e)

    @staticmethod
    def register_site_signature_hook(func):
        HookManager.SITE_SIGNATURE.append(func)

    @staticmethod
    def register_site_authentication_hook(func):
        HookManager.SITE_AUTHENTICATION.append(func)

    @staticmethod
    def register_client_authentication_hook(func):
        HookManager.CLIENT_AUTHENTICATION.append(func)

    @staticmethod
    def register_permission_check_hook(func):
        HookManager.PERMISSION_CHECK.append(func)

    @staticmethod
    def client_authentication(parm: AuthenticationParameters) -> AuthenticationReturn:
        if HookManager.CLIENT_AUTHENTICATION:
            return HookManager.CLIENT_AUTHENTICATION[0](parm)
        return AuthenticationReturn()

    @staticmethod
    def site_signature(parm: SignatureParameters) -> SignatureReturn:
        if HookManager.SITE_SIGNATURE:
            return HookManager.SITE_SIGNATURE[0](parm)
        return SignatureReturn()

    @staticmethod
    def site_authentication(parm: AuthenticationParameters) -> AuthenticationReturn:
        if HookManager.SITE_AUTHENTICATION:
            return HookManager.SITE_AUTHENTICATION[0](parm)
        return AuthenticationReturn()

    @staticmethod
    def permission_check(parm: PermissionCheckParameters) -> PermissionReturn:
        if HookManager.PERMISSION_CHECK:
            for permission_check_func in HookManager.PERMISSION_CHECK:
                result = permission_check_func(parm)
                if result.code != ReturnCode.Base.SUCCESS:
                    return result
        return PermissionReturn()
