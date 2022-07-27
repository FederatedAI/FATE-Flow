import base64
import json

from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import MD5

from fate_flow.db.key_manager import RsaKeyManager
from fate_flow.entity import RetCode
from fate_flow.entity.types import SiteKeyName
from fate_flow.hook import HookManager
from fate_flow.hook.common.parameters import SignatureParameters, AuthenticationParameters, AuthenticationReturn, \
    SignatureReturn
from fate_flow.settings import PARTY_ID


@HookManager.register_site_signature_hook
def signature(parm: SignatureParameters) -> SignatureReturn:
    private_key = RsaKeyManager.get_key(parm.party_id, key_name=SiteKeyName.PRIVATE.value)
    if not private_key:
        raise Exception(f"signature error: no found party id {parm.party_id} private key")
    sign= PKCS1_v1_5.new(RSA.importKey(private_key)).sign(MD5.new(json.dumps(parm.body).encode()))
    return SignatureReturn(site_signature=base64.b64encode(sign).decode())


@HookManager.register_site_authentication_hook
def authentication(parm: AuthenticationParameters) -> AuthenticationReturn:
    party_id = parm.src_party_id if parm.src_party_id and str(parm.src_party_id) != "0" else PARTY_ID
    public_key = RsaKeyManager.get_key(party_id=party_id, key_name=SiteKeyName.PUBLIC.value)
    if not public_key:
        raise Exception(f"signature error: no found party id {party_id} public key")
    verifier = PKCS1_v1_5.new(RSA.importKey(public_key))
    if verifier.verify(MD5.new(json.dumps(parm.body).encode()), base64.b64decode(parm.site_signature)) is True:
        return AuthenticationReturn()
    else:
        return AuthenticationReturn(code=RetCode.AUTHENTICATION_ERROR, message="authentication failed")
