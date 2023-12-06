import datetime
import json


class ColumnInfo(dict):
    """特征信息"""
    name = ''  # 特征名称
    type = ''  # 特征类型

    def __init__(self, name: str, type: str):
        super().__init__()
        self.name = name
        self.type = type

    def __getattr__(self, key):
        return self[key]

    def __setattr__(self, key, value):
        self[key] = value


class Meta(object):
    count = 0  # 数据量
    partitions = 1  # 分区数
    column_info = []  # 特征信息
    description = ''  # 数据描述
    create_time = datetime.datetime.now()  # 数据创建时间
    expire_time = create_time + datetime.timedelta(days=365)  # 数据有效截至时间
    file_type = ''  # 数据集文件类型
    data_type = 'dense'  # 数据集类型
    metadata = {}

    def __init__(self, column_info: list, options: str, partition: int, description: str, metadata: dict):
        self.column_info = column_info
        self.options = options
        self.partitions = partition
        self.description = description
        self.metadata = metadata

    def meta_output(self):
        return json.dumps({
            "column_info": self.column_info,
            "options": self.options,
            "partitions": self.partitions,
            "description": self.description,
            "data_type": self.data_type,
            "file_type": self.file_type,
            "create_time": self.create_time.timestamp(),
            "expire_time": self.expire_time.timestamp(),
            "count": self.count,
            "metadata": self.metadata
        })

    def meta_input(self, meta_data):
        meta_json = json.loads(meta_data)
        self.column_info = meta_json.get('column_info')
        self.column_info = [ColumnInfo(**c) for c in self.column_info]  # 转成对象
        self.options = meta_json.get('options')
        self.partitions = meta_json.get('partitions')
        self.description = meta_json.get('description')
        self.count = meta_json.get('count')
        self.create_time = datetime.datetime.fromtimestamp(meta_json.get('create_time'))
        self.expire_time = datetime.datetime.fromtimestamp(meta_json.get('expire_time'))
        self.file_type = meta_json.get('file_type')
        self.data_type = meta_json.get('data_type')
        self.metadata = meta_json.get("metadata")
