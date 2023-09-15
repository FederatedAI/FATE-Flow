import ast
import os.path
import re
from importlib.util import spec_from_file_location, module_from_spec
from pathlib import Path

import fate_flow
from fate_flow.runtime.system_settings import HOST, HTTP_PORT, API_VERSION

base_path = f"/{API_VERSION}"
FATE_FLOW_HOME = os.path.dirname(fate_flow.__file__)
DOC_BASE = os.path.join(os.path.dirname(os.path.dirname(FATE_FLOW_HOME)), "doc", "build")
swagger_py_file = os.path.join(DOC_BASE, "swagger_server.py")


def search_pages_path(pages_dir):
    return [path for path in pages_dir.glob('*_app.py') if not path.name.startswith('.')]


def read_desc_script(files):
    with open(files, "r") as file:
        content = file.read()

    pattern = r'(\w+)\s*=\s*"([^"]+)"'
    variables = dict(re.findall(pattern, content))
    return variables


def scan_client_app(file_path, variables):
    function_info = {}
    for _path in file_path:
        page_name = _path.stem.rstrip('app').rstrip("_")
        module_name = '.'.join(_path.parts[_path.parts.index('apps') - 1:-1] + (page_name,))
        spec = spec_from_file_location(module_name, _path)
        page = module_from_spec(spec)
        page_name = getattr(page, 'page_name', page_name)
        if page_name not in function_info:
            function_info[page_name] = []
        with open(str(_path), 'r') as file:
            tree = ast.parse(file.read())

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                function_name = node.name
                function_params = []
                function_route = None
                function_method = None
                function_params_desc = {}

                for arg in node.args.args:
                    function_params.append(arg.arg)

                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute):
                        if decorator.func.attr == 'route':
                            function_route = decorator.args[0].s
                            if isinstance(decorator.keywords, list):
                                for keyword in decorator.keywords:
                                    if keyword.arg == 'methods':
                                        function_method = keyword.value.elts[0].s

                        else:
                            params_value = ""
                            params_name = ""
                            for key in decorator.keywords:
                                if key.arg == 'desc':
                                    params_value = key.value.id
                                else:
                                    params_name = key.arg

                            if params_name:
                                function_params_desc[params_name] = variables.get(params_value, "")
                function_info[page_name].append({
                    'function_name': function_name,
                    'function_route': function_route,
                    'function_method': function_method,
                    'function_params_desc': function_params_desc,
                })

    return function_info


def generate_transfer_doc(function_info):
    script = f"""
from flask import Flask
from flask_restx import Api, Resource, Swagger
from werkzeug.utils import cached_property


class RSwagger(Swagger):
    def as_dict_v2(self):
        _dict = self.as_dict()
        _dict["basePath"] = "{base_path}"
        return _dict

    def operation_id_for(self, doc, method):
        return (
            doc[method].get("operationId")
            if "operationId" in doc[method]
            else self.api.default_id(doc["name"], method)
        )

    def description_for(self, doc, method):
        return doc[method].get("description")


class RApi(Api):
    @cached_property
    def __schema__(self):
        if not self._schema:
            try:
                self._schema = RSwagger(self).as_dict_v2()
            except Exception:
                msg = "Unable to render schema"
                log.exception(msg)
                return msg
        return self._schema


app = Flask(__name__)
api = RApi(app, version="{fate_flow.__version__}", title="FATE Flow restful api")
"""

    for page_name in function_info.keys():
        script += f"""
{page_name} = api.namespace("{page_name}", description="{page_name}-Related Operations")
"""
    for page_name, infos in function_info.items():
        for info in infos:
            function_name = ''.join([word.capitalize() for word in info['function_name'].split("_")])
            function_route = info['function_route']
            function_method = info['function_method']
            function_params_desc = info['function_params_desc']

            script += f"""

@{page_name}.route('{function_route}')
class {function_name}(Resource):
    @api.doc(params={function_params_desc}, operationId='{function_method.lower()}_{page_name}_{function_name}', descrption='this is a test')
    def {function_method.lower()}(self):
        '''

        '''
        # Your code here
        return 
"""
    script += f"""
    
if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    else:
        port = 5000
    app.run(port=port)
"""
    return script


if __name__ == '__main__':
    file_dir = search_pages_path(Path(FATE_FLOW_HOME) / 'apps/client')
    variables = read_desc_script(Path(FATE_FLOW_HOME) / 'apps/desc.py')
    function_info = scan_client_app(file_dir, variables)
    transfer_doc_script = generate_transfer_doc(function_info)
    with open(swagger_py_file, 'w', encoding='utf-8') as file:
        file.write(transfer_doc_script)
