import json
import os.path
import subprocess
import sys
import threading

import requests


def run_script(script_path, *args):
    result = subprocess.run(['python', script_path, *args])
    return result.stderr


if __name__ == '__main__':
    base_dir = os.path.dirname(__file__)
    build_path = os.path.join(base_dir, 'build_swagger_server.py')

    thread = threading.Thread(target=run_script, args=(build_path,))
    thread.start()
    #
    thread.join()
    build_path = os.path.join(base_dir, 'swagger_server.py')
    port = "50000"
    server = threading.Thread(target=run_script, args=(build_path, port))

    result = server.start()

    import time
    time.sleep(3)
    data = requests.get(url=f"http://127.0.0.1:{port}/swagger.json").text
    data = json.loads(data)
    swagger_file = os.path.join(os.path.dirname(base_dir), "swagger", "swagger.json")
    os.makedirs(os.path.dirname(swagger_file), exist_ok=True)
    with open(swagger_file, "w") as fw:
        json.dump(data, fw, indent=4)
    print("build success!")
    sys.exit()
