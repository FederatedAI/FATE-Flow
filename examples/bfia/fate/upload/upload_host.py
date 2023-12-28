import os
import tempfile

from fate_flow.adapter.bfia.container.wraps.wraps import DataIo
from fate_flow.components.components.upload import Upload, UploadParam
from fate_flow.entity.spec.dag import Metadata


def upload_data(s3_address, namespace, name, file, meta, head=True, partitions=16, extend_sid=True, storage_engine="standalone"):
    upload_object = Upload()
    params = {
        'name': name,
        'namespace': namespace,
        'file': file,
        'storage_engine': storage_engine,
        'head': head,
        'partitions': partitions,
        'extend_sid': extend_sid,
        'meta': meta
    }
    params = UploadParam(**params)

    with tempfile.TemporaryDirectory() as data_home:
        os.environ["STANDALONE_DATA_HOME"] = data_home
        data_meta = upload_object.run(params).get("data_meta")

        metadata = Metadata(metadata=dict(options=dict(partitions=partitions), schema=data_meta))
        data_path = os.path.join(data_home, namespace, name)
        engine = DataIo(s3_address)
        engine.upload_to_s3(data_path, name=name, namespace=namespace, metadata=metadata.dict())


if __name__ == "__main__":
    s3_address = "s3://127.0.0.1:9000?username=admin&password=12345678"
    namespace = "upload"
    name = "host"
    file = 'examples/data/breast_hetero_host.csv'

    meta = {
        "delimiter": ",",
        "match_id_name": "id"
    }
    upload_data(s3_address=s3_address, namespace=namespace, name=name, file=file, meta=meta)
