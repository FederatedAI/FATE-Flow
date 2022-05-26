import importlib

from fate_flow.hook.parameters import SignatureParameters, AuthenticationParameters, PermissionCheckParameters, \
    SignatureReturn, AuthenticationReturn, PermissionReturn
from fate_flow.settings import HOOK_MODULE


class HookManager:
    SIGNATURE = None
    AUTHENTICATION = None
    PERMISSION_CHECK = None

    @staticmethod
    def init():
        importlib.import_module(HOOK_MODULE)

    @staticmethod
    def register_signature_hook(fun):
        HookManager.SIGNATURE = fun

    @staticmethod
    def register_authentication_hook(fun):
        HookManager.AUTHENTICATION = fun

    @staticmethod
    def register_permission_check_hook(fun):
        HookManager.PERMISSION_CHECK = fun

    @staticmethod
    def signature(parm: SignatureParameters) -> SignatureReturn:
        if HookManager.SIGNATURE is not None:
            return HookManager.SIGNATURE(parm)
        return SignatureReturn()

    @staticmethod
    def authentication(parm: AuthenticationParameters) -> AuthenticationReturn:
        if HookManager.AUTHENTICATION is not None:
            return HookManager.AUTHENTICATION(parm)
        return AuthenticationReturn()

    @staticmethod
    def permission_check(parm: PermissionCheckParameters) -> PermissionReturn:
        if HookManager.PERMISSION_CHECK is not None:
            return HookManager.PERMISSION_CHECK(parm)
        return PermissionReturn()
