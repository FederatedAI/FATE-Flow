#
#  Copyright 2019 The FATE Authors. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
import logging
import sys
from base64 import b64encode
from hmac import HMAC
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from time import time
from urllib.parse import quote, urlencode

from flask import Blueprint, Flask, request

from fate_arch.common.base_utils import CustomJSONEncoder
from fate_flow.settings import (API_VERSION, HTTP_APP_KEY, HTTP_SECRET_KEY, MAX_TIMESTAMP_INTERVAL, access_logger,
                                stat_logger)
from fate_flow.utils.api_utils import error_response, server_error_response


__all__ = ['app']

logger = logging.getLogger('flask.app')
for h in access_logger.handlers:
    logger.addHandler(h)

app = Flask(__name__)
app.url_map.strict_slashes = False
app.errorhandler(500)(server_error_response)
app.json_encoder = CustomJSONEncoder

pages_dir = [
    Path(__file__).parent,
    Path(__file__).parent.parent / 'scheduling_apps'
]
pages_path = [j for i in pages_dir for j in i.glob('*_app.py')]

for path in pages_path:
    page_name = path.stem.rstrip('_app')
    module_name = '.'.join(path.parts[path.parts.index('fate_flow'):-1] + (page_name, ))

    spec = spec_from_file_location(module_name, path)
    page = module_from_spec(spec)
    page.app = app
    page.manager = Blueprint(page_name, module_name)
    sys.modules[module_name] = page
    spec.loader.exec_module(page)

    if not isinstance(page.manager, Blueprint):
        raise TypeError(f'page.manager should be {Blueprint!r}, got {type(page.manager)}. filepath: {path!s}')

    api_version = getattr(page, 'api_version', API_VERSION)
    page_name = getattr(page, 'page_name', page_name)

    app.register_blueprint(page.manager, url_prefix=f'/{api_version}/{page_name}')

stat_logger.info('imported pages: %s', ' '.join(str(path) for path in pages_path))


@app.before_request
def authentication():
    if request.json and request.form:
        return error_response(400)

    if not (HTTP_APP_KEY and HTTP_SECRET_KEY):
        return

    for i in [
        'TIMESTAMP',
        'NONCE',
        'APP_KEY',
        'SIGNATURE',
    ]:
        if not request.headers.get(i):
            return error_response(401)

    try:
        timestamp = int(request.headers['TIMESTAMP']) / 1000
    except Exception:
        return error_response(400, 'Invalid TIMESTAMP')

    now = time()
    if not now - MAX_TIMESTAMP_INTERVAL < timestamp < now + MAX_TIMESTAMP_INTERVAL:
        return error_response(425, f'TIMESTAMP is more than {MAX_TIMESTAMP_INTERVAL} seconds away from the server time')

    if not request.headers['NONCE']:
        return error_response(400, 'Invalid NONCE')

    if request.headers['APP_KEY'] != HTTP_APP_KEY:
        return error_response(401, 'Unknown APP_KEY')

    signature = b64encode(HMAC(HTTP_SECRET_KEY.encode('ascii'), b'\n'.join([
        request.headers['TIMESTAMP'].encode('ascii'),
        request.headers['NONCE'].encode('ascii'),
        request.headers['APP_KEY'].encode('ascii'),
        request.full_path.rstrip('?').encode('ascii'),
        request.data if request.json else b'',
        # quote_via: `urllib.parse.quote` replaces spaces with `%20`
        # safe: unreserved characters from rfc3986
        urlencode(sorted(request.form.items()), quote_via=quote, safe='-._~').encode('ascii')
        if request.form else b'',
    ]), 'sha1').digest()).decode('ascii')
    if signature != request.headers['SIGNATURE']:
        return error_response(403)
