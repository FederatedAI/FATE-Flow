#
#  Copyright 2021 The FATE Authors. All Rights Reserved.
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
import abc
import atexit
import json
import socket
import time
from functools import wraps
from pathlib import Path
from queue import Queue
from threading import Thread
from urllib import parse

from kazoo.client import KazooClient
from kazoo.exceptions import NodeExistsError, NoNodeError, ZookeeperError
from kazoo.security import make_digest_acl
from shortuuid import ShortUUID

from fate_flow.db import ServiceRegistryInfo, ServerRegistryInfo
from fate_flow.db.base_models import DB
from fate_flow.entity.types import FlowInstance
from fate_flow.errors.zookeeper_error import ServiceNotSupported, ServicesError, ZooKeeperNotConfigured, \
    MissingZooKeeperUsernameOrPassword, ZooKeeperBackendError
from fate_flow.runtime.reload_config_base import ReloadConfigBase
from fate_flow.runtime.system_settings import RANDOM_INSTANCE_ID, HOST, HTTP_PORT, GRPC_PORT, ZOOKEEPER_REGISTRY, \
    ZOOKEEPER, USE_REGISTRY, NGINX_HOST, NGINX_HTTP_PORT, FATE_FLOW_MODEL_TRANSFER_ENDPOINT, SERVICE_CONF_NAME
from fate_flow.utils import conf_utils, file_utils
from fate_flow.utils.log import getLogger
from fate_flow.utils.version import get_flow_version

stat_logger = getLogger("fate_flow_stat")

model_download_endpoint = f'http://{NGINX_HOST}:{NGINX_HTTP_PORT}{FATE_FLOW_MODEL_TRANSFER_ENDPOINT}'

instance_id = ShortUUID().random(length=8) if RANDOM_INSTANCE_ID else f'flow-{HOST}-{HTTP_PORT}'
server_instance = (
    f'{HOST}:{GRPC_PORT}',
    json.dumps({
        'instance_id': instance_id,
        'timestamp': round(time.time() * 1000),
        'version': get_flow_version() or '',
        'host': HOST,
        'grpc_port': GRPC_PORT,
        'http_port': HTTP_PORT,
    }),
)


def check_service_supported(method):
    """Decorator to check if `service_name` is supported.
    The attribute `supported_services` MUST be defined in class.
    The first and second arguments of `method` MUST be `self` and `service_name`.

    :param Callable method: The class method.
    :return: The inner wrapper function.
    :rtype: Callable
    """
    @wraps(method)
    def magic(self, service_name, *args, **kwargs):
        if service_name not in self.supported_services:
            raise ServiceNotSupported(service_name=service_name)
        return method(self, service_name, *args, **kwargs)
    return magic


class ServicesDB(abc.ABC):
    """Database for storage service urls.
    Abstract base class for the real backends.

    """
    @property
    @abc.abstractmethod
    def supported_services(self):
        """The names of supported services.
        The returned list SHOULD contain `fateflow` (model download) and `servings` (FATE-Serving).

        :return: The service names.
        :rtype: list
        """
        pass

    @abc.abstractmethod
    def _insert(self, service_name, service_url, value=''):
        pass

    @check_service_supported
    def insert(self, service_name, service_url, value=''):
        """Insert a service url to database.

        :param str service_name: The service name.
        :param str service_url: The service url.
        :return: None
        """
        try:
            self._insert(service_name, service_url, value)
        except ServicesError as e:
            stat_logger.exception(e)

    @abc.abstractmethod
    def _delete(self, service_name, service_url):
        pass

    @check_service_supported
    def delete(self, service_name, service_url):
        """Delete a service url from database.

        :param str service_name: The service name.
        :param str service_url: The service url.
        :return: None
        """
        try:
            self._delete(service_name, service_url)
        except ServicesError as e:
            stat_logger.exception(e)

    def register_model(self, party_model_id, model_version):
        # todo
        pass

    def unregister_model(self, party_model_id, model_version):
        """Call `self.delete` for delete a service url from database.
        Currently, only `fateflow` (model download) urls are supported.

        :param str party_model_id: The party model id, `#` will be replaced with `_`.
        :param str model_version: The model version.
        :return: None
        """
        # todo
        pass

    def register_flow(self):
        """Call `self.insert` for insert the flow server address to databae.

        :return: None
        """
        self.insert('flow-server', *server_instance)

    def unregister_flow(self):
        """Call `self.delete` for delete the flow server address from databae.

        :return: None
        """
        self.delete('flow-server', server_instance[0])

    @abc.abstractmethod
    def _get_urls(self, service_name, with_values=False):
        pass

    @check_service_supported
    def get_urls(self, service_name, with_values=False):
        """Query service urls from database. The urls may belong to other nodes.
        Currently, only `fateflow` (model download) urls and `servings` (FATE-Serving) urls are supported.
        `fateflow` is a url containing scheme, host, port and path,
        while `servings` only contains host and port.

        :param str service_name: The service name.
        :return: The service urls.
        :rtype: list
        """
        try:
            return self._get_urls(service_name, with_values)
        except ServicesError as e:
            stat_logger.exception(e)
            return []

    def register_models(self):
        """Register all service urls of each model to database on this node.

        :return: None
        """
        # todo:
        pass

    def unregister_models(self):
        """Unregister all service urls of each model to database on this node.

        :return: None
        """
        # todo
        pass

    def get_servers(self, to_dict=False):
        servers = {}
        for znode, value in self.get_urls('flow-server', True):
            instance = FlowInstance(**json.loads(value))
            _id = instance.instance_id
            if to_dict:
                instance = instance.to_dict()
            servers[_id] = instance
        return servers


class ZooKeeperDB(ServicesDB):
    """ZooKeeper Database

    """
    znodes = ZOOKEEPER_REGISTRY
    supported_services = znodes.keys()

    def __init__(self):
        hosts = ZOOKEEPER.get('hosts')
        if not isinstance(hosts, list) or not hosts:
            raise ZooKeeperNotConfigured()

        client_kwargs = {'hosts': hosts}

        use_acl = ZOOKEEPER.get('use_acl', False)
        if use_acl:
            username = ZOOKEEPER.get('user')
            password = ZOOKEEPER.get('password')
            if not username or not password:
                raise MissingZooKeeperUsernameOrPassword()

            client_kwargs['default_acl'] = [make_digest_acl(username, password, all=True)]
            client_kwargs['auth_data'] = [('digest', ':'.join([username, password]))]

        try:
            # `KazooClient` is thread-safe, it contains `_thread.RLock` and can not be pickle.
            # So be careful when using `self.client` outside the class.
            self.client = KazooClient(**client_kwargs)
            self.client.start()
        except ZookeeperError as e:
            raise ZooKeeperBackendError(error_message=repr(e))

        atexit.register(self.client.stop)

        self.znodes_list = Queue()
        Thread(target=self._watcher).start()

    def _insert(self, service_name, service_url, value=''):
        znode = self._get_znode_path(service_name, service_url)
        value = value.encode('utf-8')

        try:
            self.client.create(znode, value, ephemeral=True, makepath=True)
        except NodeExistsError:
            stat_logger.warning(f'Znode `{znode}` exists, add it to watch list.')
            self.znodes_list.put((znode, value))
        except ZookeeperError as e:
            raise ZooKeeperBackendError(error_message=repr(e))

    def _delete(self, service_name, service_url):
        znode = self._get_znode_path(service_name, service_url)

        try:
            self.client.delete(znode)
        except NoNodeError:
            stat_logger.warning(f'Znode `{znode}` not found, ignore deletion.')
        except ZookeeperError as e:
            raise ZooKeeperBackendError(error_message=repr(e))

    def _get_znode_path(self, service_name, service_url):
        """Get the znode path by service_name.

        :param str service_name: The service name.
        :param str service_url: The service url.
        :return: The znode path composed of `self.znodes[service_name]` and escaped `service_url`.
        :rtype: str

        """

        return '/'.join([self.znodes[service_name], parse.quote(service_url, safe='')])

    def _get_urls(self, service_name, with_values=False):
        try:
            _urls = self.client.get_children(self.znodes[service_name])
        except ZookeeperError as e:
            raise ZooKeeperBackendError(error_message=repr(e))

        urls = []

        for url in _urls:
            url = parse.unquote(url)
            data = ''
            znode = self._get_znode_path(service_name, url)

            if service_name == 'servings':
                url = parse.urlparse(url).netloc or url

            if with_values:
                try:
                    data = self.client.get(znode)
                except NoNodeError:
                    stat_logger.warning(f'Znode `{znode}` not found, return empty value.')
                except ZookeeperError as e:
                    raise ZooKeeperBackendError(error_message=repr(e))
                else:
                    data = data[0].decode('utf-8')

            urls.append((url, data) if with_values else url)

        return urls

    def _watcher(self):
        while True:
            znode, value = self.znodes_list.get()

            try:
                self.client.create(znode, value, ephemeral=True, makepath=True)
            except NodeExistsError:
                stat = self.client.exists(znode)

                if stat is not None:
                    if stat.owner_session_id is None:
                        stat_logger.warning(f'Znode `{znode}` is not an ephemeral node.')
                        continue
                    if stat.owner_session_id == self.client.client_id[0]:
                        stat_logger.warning(f'Duplicate znode `{znode}`.')
                        continue

                self.znodes_list.put((znode, value))


class FallbackDB(ServicesDB):
    """Fallback Database.
       This class get the service url from `conf/service_conf.yaml`
       It cannot insert or delete the service url.

    """
    supported_services = (
        'fateflow',
        'flow-server',
        'servings',
    )

    def _insert(self, *args, **kwargs):
        pass

    def _delete(self, *args, **kwargs):
        pass

    def _get_urls(self, service_name, with_values=False):
        if service_name == 'fateflow':
            return [(model_download_endpoint, '')] if with_values else [model_download_endpoint]
        if service_name == 'flow-server':
            return [server_instance] if with_values else [server_instance[0]]

        urls = getattr(ServerRegistry, service_name.upper(), [])
        if isinstance(urls, dict):
            urls = urls.get('hosts', [])
        if not isinstance(urls, list):
            urls = [urls]
        return [(url, '') for url in urls] if with_values else urls


class ServerRegistry(ReloadConfigBase):
    @classmethod
    def load(cls):
        cls.load_server_info_from_conf()
        cls.load_server_info_from_db()

    @classmethod
    def register(cls, server_name, host, port, protocol):
        server_name = server_name.upper()
        server_info = {
            "host": host,
            "port": port,
            "protocol": protocol
        }
        cls.save_server_info_to_db(server_name, host, port=port, protocol=protocol)
        setattr(cls, server_name, server_info)
        server_info.update({"server_name": server_name})
        return server_info

    @classmethod
    def delete_server_from_db(cls, server_name):
        operate = ServerRegistryInfo.delete().where(ServerRegistryInfo.f_server_name == server_name.upper())
        return operate.execute()

    @classmethod
    def parameter_check(cls, service_info):
        if "host" in service_info and "port" in service_info:
            cls.connection_test(service_info.get("host"), service_info.get("port"))

    @classmethod
    def connection_test(cls, ip, port):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = s.connect_ex((ip, port))
        if result != 0:
            raise ConnectionRefusedError(f"connection refused: host {ip}, port {port}")

    @classmethod
    def query(cls, service_name, default=None):
        service_info = getattr(cls, service_name, default)
        if not service_info:
            service_info = conf_utils.get_base_config(service_name, default)
        return service_info

    @classmethod
    @DB.connection_context()
    def query_server_info_from_db(cls, server_name=None) -> [ServerRegistryInfo]:
        if server_name:
            server_list = ServerRegistryInfo.select().where(ServerRegistryInfo.f_server_name == server_name.upper())
        else:
            server_list = ServerRegistryInfo.select()
        return [server for server in server_list]

    @classmethod
    @DB.connection_context()
    def load_server_info_from_db(cls):
        for server in cls.query_server_info_from_db():
            server_info = {
                "host": server.f_host,
                "port": server.f_port,
                "protocol": server.f_protocol
            }
            setattr(cls, server.f_server_name.upper(), server_info)

    @classmethod
    def load_server_info_from_conf(cls):
        path = Path(file_utils.get_fate_flow_directory()) / 'conf' / SERVICE_CONF_NAME
        conf = file_utils.load_yaml_conf(path)
        if not isinstance(conf, dict):
            raise ValueError('invalid config file')

        local_path = path.with_name(f'local.{SERVICE_CONF_NAME}')
        if local_path.exists():
            local_conf = file_utils.load_yaml_conf(local_path)
            if not isinstance(local_conf, dict):
                raise ValueError('invalid local config file')
            conf.update(local_conf)
        for k, v in conf.items():
            if isinstance(v, dict):
                setattr(cls, k.upper(), v)

    @classmethod
    @DB.connection_context()
    def save_server_info_to_db(cls, server_name, host, port, protocol="http"):
        server_info = {
            "f_server_name": server_name,
            "f_host": host,
            "f_port": port,
            "f_protocol": protocol
        }
        entity_model, status = ServerRegistryInfo.get_or_create(
            f_server_name=server_name,
            defaults=server_info)
        if status is False:
            for key in server_info:
                setattr(entity_model, key, server_info[key])
            entity_model.save(force_insert=False)


class ServiceRegistry:
    @classmethod
    @DB.connection_context()
    def load_service(cls, server_name, service_name) -> [ServiceRegistryInfo]:
        server_name = server_name.upper()
        service_registry_list = ServiceRegistryInfo.query(server_name=server_name, service_name=service_name)
        return [service for service in service_registry_list]

    @classmethod
    @DB.connection_context()
    def save_service_info(cls, server_name, service_name, uri, method="POST", server_info=None, params=None, data=None, headers=None, protocol="http"):
        server_name = server_name.upper()
        if not server_info:
            server_list = ServerRegistry.query_server_info_from_db(server_name=server_name)
            if not server_list:
                raise Exception(f"no found server {server_name}")
            server_info = server_list[0]
            url = f"{server_info.f_protocol}://{server_info.f_host}:{server_info.f_port}{uri}"
        else:
            url = f"{server_info.get('protocol', protocol)}://{server_info.get('host')}:{server_info.get('port')}{uri}"
        service_info = {
            "f_server_name": server_name,
            "f_service_name": service_name,
            "f_url": url,
            "f_method": method,
            "f_params": params if params else {},
            "f_data": data if data else {},
            "f_headers": headers if headers else {}
        }
        entity_model, status = ServiceRegistryInfo.get_or_create(
            f_server_name=server_name,
            f_service_name=service_name,
            defaults=service_info)
        if status is False:
            for key in service_info:
                setattr(entity_model, key, service_info[key])
            entity_model.save(force_insert=False)

    @classmethod
    @DB.connection_context()
    def delete(cls, server_name, service_name):
        server_name = server_name.upper()
        operate = ServiceRegistryInfo.delete().where(ServiceRegistryInfo.f_server_name == server_name.upper(),
                                                     ServiceRegistryInfo.f_service_name == service_name)
        return operate.execute()


def service_db():
    """Initialize services database.
    Currently only ZooKeeper is supported.

    :return ZooKeeperDB if `use_registry` is `True`, else FallbackDB.
            FallbackDB is a compatible class and it actually does nothing.
    """
    if not USE_REGISTRY:
        return FallbackDB()
    if isinstance(USE_REGISTRY, str):
        if USE_REGISTRY.lower() == 'zookeeper':
            return ZooKeeperDB()
    # backward compatibility
    return ZooKeeperDB()
