from base64 import b64encode
from hmac import HMAC
from time import time
from urllib.parse import quote, urlencode

from fate_flow.settings import HTTP_APP_KEY, HTTP_SECRET_KEY, MAX_TIMESTAMP_INTERVAL
from fate_flow.entity import RetCode
from fate_flow.hook import HookManager
from fate_flow.hook.common.parameters import  ClientAuthenticationReturn, ClientAuthenticationParameters


@HookManager.register_client_authentication_hook
def authentication(parm: ClientAuthenticationParameters) -> ClientAuthenticationReturn:
    if not (HTTP_APP_KEY and HTTP_SECRET_KEY):
        return ClientAuthenticationReturn(code=RetCode.AUTHENTICATION_ERROR,
                                          message=f"settings HTTP_APP_KEY and HTTP_SECRET_KEY is None")

    requirement_parm = ['TIMESTAMP', 'NONCE', 'APP_KEY', 'SIGNATURE']
    for _p in requirement_parm:
        if not parm.headers.get(_p):
            return ClientAuthenticationReturn(code=RetCode.AUTHENTICATION_ERROR,
                                              message=f"requirement headers parameters: {requirement_parm}")
    try:
        timestamp = int(parm.headers['TIMESTAMP']) / 1000
    except Exception:
        return ClientAuthenticationReturn(code=RetCode.AUTHENTICATION_ERROR, message="Invalid TIMESTAMP")
    now = time()
    if not now - MAX_TIMESTAMP_INTERVAL < timestamp < now + MAX_TIMESTAMP_INTERVAL:
        return ClientAuthenticationReturn(
            code=RetCode.AUTHENTICATION_ERROR,
            message=f'TIMESTAMP is more than {MAX_TIMESTAMP_INTERVAL} seconds away from the server time'
        )

    if not parm.headers['NONCE']:
        return ClientAuthenticationReturn(
            code=RetCode.AUTHENTICATION_ERROR,
            message='Invalid NONCE'
        )

    if parm.headers['APP_KEY'] != HTTP_APP_KEY:
        return ClientAuthenticationReturn(
            code=RetCode.AUTHENTICATION_ERROR,
            message='Unknown APP_KEY'
        )

    # authentication
    signature = b64encode(HMAC(HTTP_SECRET_KEY.encode('ascii'), b'\n'.join([
        parm.headers['TIMESTAMP'].encode('ascii'),
        parm.headers['NONCE'].encode('ascii'),
        parm.headers['APP_KEY'].encode('ascii'),
        parm.full_path.rstrip('?').encode('ascii'),
        parm.data if parm.json else b'',
        # quote_via: `urllib.parse.quote` replaces spaces with `%20`
        # safe: unreserved characters from rfc3986
        urlencode(sorted(parm.form.items()), quote_via=quote, safe='-._~').encode('ascii')
        if parm.form else b'',
    ]), 'sha1').digest()).decode('ascii')
    if signature != parm.headers['SIGNATURE']:
        return ClientAuthenticationReturn(
            code=RetCode.AUTHENTICATION_ERROR,
            message='signature authentication failed'
        )
    return ClientAuthenticationReturn()