import os
import tarfile
import uuid
from tempfile import TemporaryDirectory

from .client import S3Client
from .consts import S3_BUCKET_NAME, S3_OBJECT_KEY, S3_SAVE_PATH, S3_META_KEY
from .meta import Meta, ColumnInfo


class Table(Meta):
    """数据实体"""
    name = ''  # 数据表名称
    namespace = ''  # 数据表明明空间

    def __init__(self, name: str, namespace: str, column_info: list = None, partition: int = 1, options: str = '',
                 description: str = '', metadata={}):
        super().__init__(column_info=column_info, partition=partition, options=options, description=description, metadata=metadata)
        self.name = name
        self.namespace = namespace

    def upload(self, local_path: str, overwrite: bool = True, callback_func=None, file_type: str = 'csv'):
        """上传本地文件"""
        pass

    def download(self, local_path: str, overwrite: bool = True, callback_func=None):
        """下载文件"""
        pass

    def read(self, partition_index: int = 1, callback_func=None) -> bytes:
        """读取文件"""
        pass

    def write(self, data: bytes, partition_id: int = 1, overwrite: bool = True, callback_func=None,
              file_type: str = 'csv'):
        """写文件"""
        pass

    def set_column_info(self, column_info: list):
        """设置特征信息"""
        pass

    def get_column_info(self) -> list:
        """获取特征信息"""
        pass

    def set_description(self, description: str):
        """设置description"""
        pass

    def get_description(self) -> str:
        """获取description"""
        pass

    def get_partitions(self) -> list:
        """获取分区集合"""
        pass


class S3Table(Table):

    def __init__(self, **kwargs):
        self.s3_url = kwargs.pop('url')
        self.s3_username = kwargs.pop('username')
        self.s3_password = kwargs.pop('password')
        super().__init__(**kwargs)

    def upload(self, local_path: str, overwrite: bool = True, callback_func=None, file_type: str = 'csv'):
        self.file_type = file_type

        client = S3Client(url=self.s3_url, username=self.s3_username, password=self.s3_password)
        if not os.path.exists(local_path):
            raise ValueError('路径文件不存在')
        # if os.path.isdir(local_path):
        #     raise ValueError('暂不支持文件夹')

        # # 统计行数
        # with open(local_path, 'r') as f:
        #     lines = f.readlines()
        #     self.count = len(lines) - 1  # 去除首行

        # TODO: 分区暂固定为0
        p_idx = 0
        # 是否覆盖
        key = S3_OBJECT_KEY.format(namespace=self.namespace, name=self.name, partition=p_idx)
        object_exist = client.object_exist(bucket=S3_BUCKET_NAME, key=key)
        if object_exist and not overwrite:
            raise ValueError(f'namespace:{self.namespace}, name:{self.name} object已存在，如需覆盖请配置overwrite为True')

        client.upload_file(file_path=local_path, bucket=S3_BUCKET_NAME,
                           key=S3_OBJECT_KEY.format(namespace=self.namespace, name=self.name, partition=p_idx))

        if callback_func is not None:
            callback_func()

    def download(self, local_path: str, overwrite: bool = True, callback_func=None):
        if os.path.exists(local_path) and not overwrite:
            raise ValueError(f'已存在文件{local_path}, 如需覆盖请配置overwrite为True')
        client = S3Client(url=self.s3_url, username=self.s3_username, password=self.s3_password)
        # TODO: 分区暂固定为0
        p_idx = 0
        client.download_file(file_path=local_path, bucket=S3_BUCKET_NAME, key=S3_OBJECT_KEY.format(namespace=self.namespace, name=self.name, partition=p_idx))

        if callback_func is not None:
            callback_func()

    def read(self, partition_index: int = 1, callback_func=None) -> bytes:
        # TODO: 分区暂固定为0
        partition_index = 0
        client = S3Client(url=self.s3_url, username=self.s3_username, password=self.s3_password)
        key = S3_OBJECT_KEY.format(namespace=self.namespace, name=self.name, partition=partition_index)

        if not client.object_exist(bucket=S3_BUCKET_NAME, key=key):
            raise ValueError(f'namespace:{self.namespace}, name:{self.name} object不存在')

        response = client.get_object(bucket=S3_BUCKET_NAME, key=key)
        data = response.get('Body').read()
        if callback_func:
            callback_func()
        return data

    def write(self, data: bytes, partition_id: int = 1, overwrite: bool = True, callback_func=None,
              file_type: str = 'csv'):
        self.file_type = file_type
        if data.endswith(b'\n'):
            self.count = data.count(b'\n') - 1  # 统计\n数目判断行数
        else:
            self.count = data.count(b'\n')  # 统计\n数目判断行数
        # TODO: 分区暂固定为0
        partition_index = 0
        client = S3Client(url=self.s3_url, username=self.s3_username, password=self.s3_password)
        key = S3_OBJECT_KEY.format(namespace=self.namespace, name=self.name, partition=partition_index)

        object_exist = client.object_exist(bucket=S3_BUCKET_NAME, key=key)
        if object_exist and not overwrite:
            raise ValueError(f'namespace:{self.namespace}, name:{self.name} object已存在，如需覆盖请配置overwrite为True')
        client.put_object(body=data, bucket=S3_BUCKET_NAME, key=key)

    def get_path(self) -> str:
        """获取s3储存路径"""
        return 's3://' + S3_BUCKET_NAME + S3_SAVE_PATH.format(namespace=self.namespace, name=self.name)

    def set_column_info(self, column_info: list):
        for c in column_info:
            assert isinstance(c, ColumnInfo), 'column_info数据类型需为ColumnInfo'

        self.column_info = column_info
        client = S3Client(url=self.s3_url, username=self.s3_username, password=self.s3_password)
        client.put_object(bucket=S3_BUCKET_NAME, key=S3_META_KEY.format(namespace=self.namespace, name=self.name),
                          body=self.meta_output())

    def get_column_info(self):
        return self.column_info

    def set_description(self, description: str):
        self.description = description
        client = S3Client(url=self.s3_url, username=self.s3_username, password=self.s3_password)
        client.put_object(bucket=S3_BUCKET_NAME, key=S3_META_KEY.format(namespace=self.namespace, name=self.name),
                          body=self.meta_output())

    def get_description(self) -> str:
        return self.description

    def get_partitions(self) -> list:
        # TODO: 分区暂固定为0
        return ['data_0']


class FateTable(S3Table):
    def upload_local_data(self, path, overwrite: bool = True, callback_func=None, file_type: str = 'csv'):
        with TemporaryDirectory() as output_tmp_dir:
            if os.path.isdir(path):
                temp_path = os.path.join(output_tmp_dir, str(uuid.uuid1()))
                self._tar(path, temp_path)
                path = temp_path
            self.upload(path, overwrite, callback_func, file_type)

    def download_data_to_local(self, local_path):
        with TemporaryDirectory() as output_tmp_dir:
            temp_path = os.path.join(output_tmp_dir, str(uuid.uuid1()))
            self.download(local_path=temp_path)
            self._x_tar(temp_path, local_path)

    @staticmethod
    def _tar(source_directory,  target_archive):
        with tarfile.open(fileobj=open(target_archive, "wb"), mode='w:gz') as tar:
            for root, _, files in os.walk(source_directory):
                for file in files:
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, source_directory)
                    tar.add(full_path, rel_path)

    @staticmethod
    def _x_tar(path, download_path):
        tar = tarfile.open(path, "r:gz")
        file_names = tar.getnames()
        for file_name in file_names:
            tar.extract(file_name, download_path)
