from fate_flow.hook import HookManager
from fate_flow.hook.common.parameters import SignatureParameters, SignatureReturn, AuthenticationParameters, \
    AuthenticationReturn


@HookManager.register_site_signature_hook
def signature(parm: SignatureParameters) -> SignatureReturn:
    return SignatureReturn()


@HookManager.register_site_authentication_hook
def authentication(parm: AuthenticationParameters) -> AuthenticationReturn:
    return AuthenticationReturn()
