import os
import tempfile

from fate_flow.adapter.bfia.container.wraps.wraps import DataIo
from fate_flow.components.components.upload import Upload, UploadParam
from fate_flow.entity.spec.dag import Metadata

# data_home = "/Users/tonly/FATE/fate_flow/temp/data"
s3_address = "s3://127.0.0.1:9000?username=admin&password=12345678"

namespace = "aaa"
name = "x"
file = 'examples/data/breast_hetero_guest.csv'

meta = {
    "delimiter": ",",
    "label_name": "y",
    "match_id_name": "id"
}


upload_object = Upload()

params = {
    'name': name,
    'namespace': namespace,
    'file': file,
    'storage_engine': 'standalone',
    'head': True,
    'partitions': 16,
    'extend_sid': True,
    'meta': meta
}
params = UploadParam(**params)

with tempfile.TemporaryDirectory() as data_home:
    os.environ["STANDALONE_DATA_HOME"] = data_home
    data_meta = upload_object.run(params).get("data_meta")

    metadata = Metadata(metadata=dict(options=dict(partitions=8), schema=data_meta))
    data_path = os.path.join(data_home, namespace, name)
    engine = DataIo(s3_address)
    engine.upload_to_s3(data_path, name=name, namespace=namespace, metadata=metadata.dict())
