import os
import shutil

import fate_flow
from setuptools import find_packages, setup, Command

packages = find_packages(".")
install_requires = [
    "apsw>=3.10",
    "Flask==2.2.5",
    "grpcio==1.62.1",
    "grpcio-tools==1.62.1",
    "requests<2.26.0",
    "urllib3==1.26.18",
    "cachetools==3.0.0",
    "filelock==3.3.1",
    "pydantic==1.10.12",
    "webargs",
    "peewee==3.17.1",
    "python-dotenv==0.13.0",
    "pyyaml",
    "networkx",
    "psutil>=5.7.0",
    "casbin_peewee_adapter",
    "casbin",
    "pymysql",
    "kazoo",
    "shortuuid",
    "cos-python-sdk-v5==1.9.27",
    "typing-extensions==4.8.0",
    "ruamel.yaml==0.16",
    "boto3"
]
extras_require = {
    "rabbitmq": ["pika==1.2.1"],
    "pulsar": ["pulsar-client==3.4.0"],
    "spark": ["pyspark"],
    "eggroll": [
        "cloudpickle==2.1.0",
        "lmdb",
        "protobuf==4.24.4",
        "grpcio==1.62.1",
        "grpcio-tools==1.62.1",
        "protobuf==4.24.4",
        "psutil>=5.7.0",
        "pynvml==11.5.0"
    ],
    "fate_flow": ["fate_flow[rabbitmq,pulsar,spark,eggroll]"],
}


CONF_NAME = "conf"
PACKAGE_NAME = "fate_flow"
ENV_NAME = "fateflow.env"
HOME = os.path.abspath("../")
CONF_PATH = os.path.join(HOME, CONF_NAME)
PACKAGE_CONF_PATH = os.path.join(HOME, "python", "fate_flow", CONF_NAME)
ENV_PATH = os.path.join(HOME, ENV_NAME)
PACKAGE_ENV_PATH = os.path.join(HOME, "python", "fate_flow", ENV_NAME)

readme_path = os.path.join(HOME, "README.md")

entry_points = {"console_scripts": ["fate_flow = fate_flow.commands.server_cli:flow_server_cli"]}

if os.path.exists(readme_path):
    with open(readme_path, "r", encoding='utf-8') as f:
        long_description = f.read()
else:
    long_description = "fate flow"


class InstallCommand(Command):
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        if os.path.exists(PACKAGE_CONF_PATH):
            shutil.rmtree(PACKAGE_CONF_PATH)
        shutil.copytree(CONF_PATH, PACKAGE_CONF_PATH)
        shutil.copyfile(ENV_PATH, PACKAGE_ENV_PATH)


setup(
    name="fate_flow",
    version=fate_flow.__version__,
    keywords=["federated learning scheduler"],
    author="FederatedAI",
    author_email="contact@FedAI.org",
    long_description_content_type="text/markdown",
    long_description=long_description,
    license="Apache-2.0 License",
    url="https://fate.fedai.org/",
    packages=packages,
    install_requires=install_requires,
    extras_require=extras_require,
    package_data={
        "fate_flow": [f"{CONF_NAME}/*", ENV_NAME, "commands/*"]
    },
    python_requires=">=3.8",
    cmdclass={
        "pre_install": InstallCommand,
    },
    entry_points=entry_points
)
