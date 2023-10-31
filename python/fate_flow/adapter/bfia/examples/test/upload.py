import engine_storage

url = "http://127.0.0.1:9000"
username = "admin"
password = "12345678"

session = engine_storage.session.S3Session(url=url, username=username, password=password)
namespace = ""
name = ""
table = session.get_table(namespace=namespace, name=name)
# table = session.create_table(namespace="1", name="2", column_info=[1, 2, 3])
# table.upload("../job/components.json")
data = table.meta_output()
print(data)
