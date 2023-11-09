import os
from urllib.parse import urlparse

from .session import S3Session


def inti_session():
    """创建客户端对象"""

    storage_str = os.getenv('system.storage')
    assert storage_str is not None, 'system.storage 配置为空'

    storage_str = urlparse(storage_str)
    storage_query = {i.split('=')[0]: i.split('=')[1] for i in storage_str.query.split('&')}
    username = storage_query.get('username')
    password = storage_query.get('password')
    url = storage_str.netloc
    service_type = storage_str.scheme

    assert url is not None, 'system.storage 配置无法解析url'
    assert username is not None, 'system.storage 配置无法解析username'
    assert password is not None, 'system.storage 配置无法解析password'
    assert service_type is not None, 'system.storage 配置无法解析service_type'

    if service_type == 's3':
        url = f"http://{url}"
        return S3Session(url=url, username=username, password=password)
    else:
        assert Exception(f'不支持相应配置, storage_service_type: {service_type}')
