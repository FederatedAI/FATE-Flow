import os
import shutil

import fate_flow
from setuptools import find_packages, setup, Command

packages = find_packages(".")
install_requires = []
extras_require = {}

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
    with open(readme_path, "r") as f:
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
        "fate_flow": [f"{CONF_NAME}/*", ENV_NAME]
    },
    python_requires=">=3.8",
    cmdclass={
        "pre_install": InstallCommand,
    },
    entry_points=entry_points
)
