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
from fate_flow.settings import API_VERSION, CLIENT_AUTHENTICATION, SITE_AUTHENTICATION, access_logger
from fate_flow.utils.api_utils import get_json_result, server_error_response


__all__ = ['app']


logger = logging.getLogger('flask.app')
for h in access_logger.handlers:
    logger.addHandler(h)

Request.json = property(lambda self: self.get_json(force=True, silent=True))

app = Flask(__name__)
app.url_map.strict_slashes = False
app.json_encoder = CustomJSONEncoder
app.errorhandler(Exception)(server_error_response)


def search_pages_path(pages_dir):
    return [path for path in pages_dir.glob('*_app.py') if not path.name.startswith('.')]


def register_page(page_path):
    page_name = page_path.stem.rstrip('_app')
    module_name = '.'.join(page_path.parts[page_path.parts.index('fate_flow'):-1] + (page_name, ))

    spec = spec_from_file_location(module_name, page_path)
    page = module_from_spec(spec)
    page.app = app
    page.manager = Blueprint(page_name, module_name)
    sys.modules[module_name] = page
    spec.loader.exec_module(page)

    page_name = getattr(page, 'page_name', page_name)
    url_prefix = f'/{API_VERSION}/{page_name}'

    app.register_blueprint(page.manager, url_prefix=url_prefix)
    return url_prefix


client_urls_prefix = [
    register_page(path)
    for path in search_pages_path(Path(__file__).parent)
]
scheduling_urls_prefix = [
    register_page(path)
    for path in search_pages_path(Path(__file__).parent.parent / 'scheduling_apps')
]


def client_authentication_before_request():
    for url_prefix in scheduling_urls_prefix:
        if request.path.startswith(url_prefix):
            return

    result = HookManager.client_authentication(ClientAuthenticationParameters(
        request.full_path, request.headers,
        request.form, request.data, request.json,
    ))

    if result.code != RetCode.SUCCESS:
        return get_json_result(result.code, result.message)


def site_authentication_before_request():
    for url_prefix in client_urls_prefix:
        if request.path.startswith(url_prefix):
            return

    result = HookManager.site_authentication(AuthenticationParameters(
        request.headers.get('src_party_id'),
        request.headers.get('site_signature'),
        request.json,
    ))

    if result.code != RetCode.SUCCESS:
        return get_json_result(result.code, result.message)


@app.before_request
def authentication_before_request():
    if CLIENT_AUTHENTICATION:
        return client_authentication_before_request()

    if SITE_AUTHENTICATION:
        return site_authentication_before_request()
