
from .client import S3Client
from .consts import S3_BUCKET_NAME, S3_META_KEY, S3_OBJECT_KEY, S3_SAVE_PATH
from .table import S3Table, FateTable


class Session(object):
    def __init__(self, url: str, username: str, password: str):
        pass

    def create_table(self, name: str, namespace: str, column_info: list = None, partition: int = 1,
                     description: str = ''):
        """创建table"""
        pass

    def get_table(self, name: str, namespace: str):
        """获取table"""
        pass

    def delete_table(self, name: str, namespace: str):
        """删除table"""
        pass

    def is_exist(self, name: str, namespace: str):
        """判断数据是否存在"""
        pass


class S3Session(Session):
    """s3服务连接实现"""
    def __init__(self, url: str, username: str, password: str):
        super(S3Session, self).__init__(url, username, password)

        self.url = url
        self.username = username
        self.password = password

        self._create_bucket()

    def _create_bucket(self):
        """创建仓库"""
        client = S3Client(url=self.url, username=self.username, password=self.password)
        response = client.list_buckets()
        bucket_names = [b.get('Name') for b in response.get('Buckets', [])]
        if S3_BUCKET_NAME not in bucket_names:
            client.create_bucket(S3_BUCKET_NAME)

    def create_table(self, name: str, namespace: str, column_info: list = None, partition: int = 1,
                     description: str = '', metadata: dict = {}):
        """创建table"""
        if partition != 1:
            raise Exception('暂不支持partition分区')
        table = FateTable(url=self.url, username=self.username, password=self.password, name=name, namespace=namespace,
                        column_info=column_info, partition=partition, description=description, metadata=metadata)
        client = S3Client(url=self.url, username=self.username, password=self.password)
        client.put_object(bucket=S3_BUCKET_NAME, key=S3_META_KEY.format(namespace=namespace, name=name),
                          body=table.meta_output())
        return table

    def get_table(self, name: str, namespace: str):
        """获取table"""
        client = S3Client(url=self.url, username=self.username, password=self.password)

        # 检查table是否存在
        if not client.object_exist(bucket=S3_BUCKET_NAME, key=S3_META_KEY.format(namespace=namespace, name=name)):
            raise ValueError('table不存在，请检查参数配置')

        # 创建空table，并读入meta数据
        meta_response = client.get_object(bucket=S3_BUCKET_NAME, key=S3_META_KEY.format(namespace=namespace, name=name))
        table = FateTable(name=name, namespace=namespace, url=self.url, username=self.username, password=self.password)
        try:
            meta_data = meta_response.get('Body').read()
        except Exception as e:
            raise Exception('读取meta数据失败')
        table.meta_input(meta_data)
        return table

    def delete_table(self, name: str, namespace: str):
        client = S3Client(url=self.url, username=self.username, password=self.password)
        key = S3_SAVE_PATH.format(namespace=namespace, name=name)
        client.delete_folder(bucket=S3_BUCKET_NAME, key=key)

    def is_exist(self, name: str, namespace: str):
        client = S3Client(url=self.url, username=self.username, password=self.password)
        return client.object_exist(bucket=S3_BUCKET_NAME, key=S3_META_KEY.format(namespace=namespace, name=name))
