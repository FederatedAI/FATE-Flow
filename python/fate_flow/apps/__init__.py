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
import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

from flask import Blueprint, Flask
from werkzeug.wrappers.request import Request

from fate_flow.settings import API_VERSION, getLogger
from fate_flow.utils.api_utils import args_error_response, server_error_response
from fate_flow.utils.base_utils import CustomJSONEncoder


__all__ = ['app']

logger = getLogger('flask.app')

Request.json = property(lambda self: self.get_json(force=True, silent=True))

app = Flask(__name__)
app.url_map.strict_slashes = False
app.errorhandler(422)(args_error_response)
app.errorhandler(Exception)(server_error_response)
app.json_encoder = CustomJSONEncoder


def register_page(page_path):
    page_name = page_path.stem.rstrip('_app')
    module_name = '.'.join(page_path.parts[page_path.parts.index('apps')-1:-1] + (page_name, ))

    spec = spec_from_file_location(module_name, page_path)
    page = module_from_spec(spec)
    page.app = app
    page.manager = Blueprint(page_name, module_name)
    sys.modules[module_name] = page
    spec.loader.exec_module(page)

    page_name = getattr(page, 'page_name', page_name)
    url_prefix = f'/{API_VERSION}/{page_name}'

    app.register_blueprint(page.manager, url_prefix=url_prefix)


for path in Path(__file__).parent.glob('*/*_app.py'):
    if path.name.startswith(('.', '_')):
        continue

    register_page(path)
