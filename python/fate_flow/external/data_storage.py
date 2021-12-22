from fate_flow.entity.types import ExternalStorage
from fate_flow.external.storage import MysqlStorage


def save_data_to_external_storage(storage_engine, address, storage_table):
    if storage_engine.upper() in {ExternalStorage.MYSQL.value}:
        with MysqlStorage(address=address, storage_table=storage_table) as storage:
            storage.save()
    else:
        raise ValueError(f"{storage_engine.upper()} is not supported")
