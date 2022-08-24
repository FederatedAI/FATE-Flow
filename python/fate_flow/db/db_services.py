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
import time
from functools import wraps
from queue import Queue
from threading import Thread
from urllib import parse

from kazoo.client import KazooClient
from kazoo.exceptions import NodeExistsError, NoNodeError, ZookeeperError
from kazoo.security import make_digest_acl
from shortuuid import ShortUUID

from fate_arch.common.versions import get_fate_version

from fate_flow.db.service_registry import ServerRegistry
from fate_flow.entity.instance import FlowInstance
from fate_flow.errors.error_services import *
from fate_flow.settings import (
    FATE_FLOW_MODEL_TRANSFER_ENDPOINT, GRPC_PORT, HOST, HTTP_PORT, NGINX_HOST, NGINX_HTTP_PORT,
    RANDOM_INSTANCE_ID, USE_REGISTRY, ZOOKEEPER, ZOOKEEPER_REGISTRY, stat_logger,
)
from fate_flow.utils.model_utils import models_group_by_party_model_id_and_model_version


model_download_endpoint = f'http://{NGINX_HOST}:{NGINX_HTTP_PORT}{FATE_FLOW_MODEL_TRANSFER_ENDPOINT}'

instance_id = ShortUUID().random(length=8) if RANDOM_INSTANCE_ID else f'flow-{HOST}-{HTTP_PORT}'
server_instance = (
    f'{HOST}:{GRPC_PORT}',
    json.dumps({
        'instance_id': instance_id,
        'timestamp': round(time.time() * 1000),
        'version': get_fate_version() or '',
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


def get_model_download_url(party_model_id, model_version):
    """Get the full url of model download.

    :param str party_model_id: The party model id, `#` will be replaced with `~`.
    :param str model_version: The model version.
    :return: The download url.
    :rtype: str
    """
    return '{endpoint}/{model_id}/{model_version}'.format(
        endpoint=model_download_endpoint,
        model_id=party_model_id.replace('#', '~'),
        model_version=model_version,
    )


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
        """Call `self.insert` for insert a service url to database.
        Currently, only `fateflow` (model download) urls are supported.

        :param str party_model_id: The party model id, `#` will be replaced with `_`.
        :param str model_version: The model version.
        :return: None
        """
        self.insert('fateflow', get_model_download_url(party_model_id, model_version))

    def unregister_model(self, party_model_id, model_version):
        """Call `self.delete` for delete a service url from database.
        Currently, only `fateflow` (model download) urls are supported.

        :param str party_model_id: The party model id, `#` will be replaced with `_`.
        :param str model_version: The model version.
        :return: None
        """
        self.delete('fateflow', get_model_download_url(party_model_id, model_version))

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
        for model in models_group_by_party_model_id_and_model_version():
            self.register_model(model.f_party_model_id, model.f_model_version)

    def unregister_models(self):
        """Unregister all service urls of each model to database on this node.

        :return: None
        """
        for model in models_group_by_party_model_id_and_model_version():
            self.unregister_model(model.f_party_model_id, model.f_model_version)

    def get_servers(self):
        servers = {}
        for znode, value in self.get_urls('flow-server', True):
            instance = FlowInstance(**json.loads(value))
            servers[instance.instance_id] = instance
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

        :example:

        >>> self._get_znode_path('fateflow', 'http://127.0.0.1:9380/v1/model/transfer/arbiter-10000_guest-9999_host-10000_model/202105060929263278441')
        '/FATE-SERVICES/flow/online/transfer/providers/http%3A%2F%2F127.0.0.1%3A9380%2Fv1%2Fmodel%2Ftransfer%2Farbiter-10000_guest-9999_host-10000_model%2F202105060929263278441'
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
