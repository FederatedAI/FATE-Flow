import ast
import re
from pathlib import Path


def search_pages_path(pages_dir):
    return [path for path in pages_dir.glob('*_app.py') if not path.name.startswith('.')]


def read_desc_script(files):

    with open(files, "r") as file:
        content = file.read()

    pattern = r'(\w+)\s*=\s*"([^"]+)"'
    variables = dict(re.findall(pattern, content))
    return variables


def scan_client_app(file_path, variables):

    function_info = []
    for _path in file_path:
        route_name = str(_path).split('\\')[-1].split('.')[0]
        if route_name == "client_app":
            _name = "app"
        elif route_name == "server_app":
            _name = "service"
        elif route_name == "log_app":
            pass
        else:
            _name = route_name.split("_")[0]

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
                            function_route = _name + decorator.args[0].s
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
                function_info.append({
                    'function_name': function_name,
                    'function_route': function_route,
                    'function_method': function_method,
                    'function_params_desc': function_params_desc,
                })

    return function_info


def generate_transfer_doc(function_info):
    script = """
from flask import Flask
from flask_restx import Api, Resource

app = Flask(__name__)
api = Api(app)
"""
    for info in function_info:
        function_name = ''.join([word.capitalize() for word in info['function_name'].split("_")])
        function_route = info['function_route']
        function_method = info['function_method']
        function_params_desc = info['function_params_desc']

        script += f"""
@api.route('/v2/{function_route}')
class {function_name}(Resource):
    @api.doc(params={function_params_desc})
    def {function_method.lower()}(self):
        '''

        '''
        # Your code here
        return 
"""
    script += f"""
if __name__ == '__main__':
    app.run()
"""
    return script


if __name__ == '__main__':

    file_dir = search_pages_path(Path(__file__).parent.parent.parent/'python/fate_flow/apps/client')
    variables = read_desc_script(Path(__file__).parent.parent.parent/'python/fate_flow/apps/desc.py')
    function_info = scan_client_app(file_dir, variables)
    transfer_doc_script = generate_transfer_doc(function_info)
    with open('flow_api_swagger.py', 'w', encoding='utf-8') as file:
        file.write(transfer_doc_script)








