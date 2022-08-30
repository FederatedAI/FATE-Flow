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
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

from flask import Blueprint, Flask, request
from werkzeug.wrappers.request import Request

from fate_arch.common.base_utils import CustomJSONEncoder
from fate_flow.entity import RetCode
from fate_flow.hook import HookManager
from fate_flow.hook.common.parameters import AuthenticationParameters, ClientAuthenticationParameters
from fate_flow.settings import (API_VERSION, access_logger, stat_logger, CLIENT_AUTHENTICATION, SITE_AUTHENTICATION)
from fate_flow.utils.api_utils import server_error_response, get_json_result

__all__ = ['app']

logger = logging.getLogger('flask.app')
for h in access_logger.handlers:
    logger.addHandler(h)

Request.json = property(lambda self: self.get_json(force=True, silent=True))

app = Flask(__name__)
app.url_map.strict_slashes = False
app.errorhandler(Exception)(server_error_response)
app.json_encoder = CustomJSONEncoder

pages_dir = [
    Path(__file__).parent,
    Path(__file__).parent.parent / 'scheduling_apps'
]
pages_path = [j for i in pages_dir for j in i.glob('*_app.py')]
scheduling_url_prefix = []
client_url_prefix = []
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
    if 'scheduling_apps' in path.parts:
        scheduling_url_prefix.append(f'/{api_version}/{page_name}')
    else:
        client_url_prefix.append(f'/{api_version}/{page_name}')


stat_logger.info('imported pages: %s', ' '.join(str(path) for path in pages_path))


@app.before_request
def authentication_before_request():
    if CLIENT_AUTHENTICATION:
        _result = client_authentication_before_request()
        if _result:
            return _result
    if SITE_AUTHENTICATION:
        _result = site_authentication_before_request()
        if _result:
            return _result


def client_authentication_before_request():
    for url_prefix in scheduling_url_prefix:
        if request.path.startswith(url_prefix):
            return
    parm = ClientAuthenticationParameters(full_path=request.full_path, headers=request.headers, form=request.form,
                                          data=request.data, json=request.json)
    result = HookManager.client_authentication(parm)
    if result.code != RetCode.SUCCESS:
        return get_json_result(result.code, result.message)


def site_authentication_before_request():
    from flask import request
    for url_prefix in client_url_prefix:
        if request.path.startswith(url_prefix):
            return
    body = request.json
    headers = request.headers
    site_signature = headers.get("site_signature")
    result = HookManager.site_authentication(
        AuthenticationParameters(site_signature=site_signature, src_party_id=headers.get("src_party_id"), body=body))
    if result.code != RetCode.SUCCESS:
        return get_json_result(result.code, result.message)
