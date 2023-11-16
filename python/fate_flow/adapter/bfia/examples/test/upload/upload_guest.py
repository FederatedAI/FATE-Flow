import yaml

from fate_flow.adapter.bfia import engine_storage

url = "http://127.0.0.1:9000"
username = "admin"
password = "12345678"

session = engine_storage.session.S3Session(url=url, username=username, password=password)

namespace = "test_data"
name = "guest"
fp = open("../data/guest/metadata")
metadata = yaml.safe_load(fp)
print(metadata)

table = session.create_table(name=name, namespace=namespace, metadata=metadata.get("metadata"), column_info=[])
table.upload("../data/guest/data_0")
