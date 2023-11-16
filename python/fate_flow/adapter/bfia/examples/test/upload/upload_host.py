import yaml

from fate_flow.adapter.bfia import engine_storage

url = "http://127.0.0.1:9000"
username = "admin"
password = "12345678"

session = engine_storage.session.S3Session(url=url, username=username, password=password)

namespace = "test_data"
name = "host"
fp = open("../data/host/metadata")
metadata = yaml.safe_load(fp)
print(metadata)

table = session.create_table(name=name, namespace=namespace, column_info=[], metadata=metadata.get("metadata"))
table.upload("../data/host/data_0")
