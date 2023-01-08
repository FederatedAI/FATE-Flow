import json
import os.path

from flask import send_file

from fate_flow.db.base_models import DB, BaseModelOperate
from fate_flow.db.db_models import PipelineModelMeta
from fate_flow.settings import MODEL_STORE_PATH


class PipelinedModel(object):
    def __init__(self, model_id, model_version, role, party_id, store_engine="file"):
        self.model_id = model_id
        self.model_version = model_version
        self.role = role
        self.party_id = party_id
        self.handle = self._set_handle(store_engine)
        self.meta_manager = ModelMeta(model_id, model_version, role, party_id)

    @classmethod
    def _set_handle(cls, handle_type):
        if handle_type == "file":
            return FileHandle()

    def save_output_model(self, task_name, model_name, component, model_file):
        self.handle.write(self.model_id, self.model_version, self.role, self.party_id, task_name, model_name, model_file)
        self.meta_manager.save(task_name=task_name, component=component)

    def read_output_model(self, task_name, model_name):
        return self.handle.read(self.model_id, self.model_version, self.role, self.party_id, task_name, model_name)


class ModelMeta(BaseModelOperate):
    def __init__(self, model_id, model_version, role, party_id):
        self.model_id = model_id
        self.model_version = model_version
        self.role = role
        self.party_id = party_id

    def save(self, task_name, component):
        meta_info = {
            "model_id": self.model_id,
            "model_version": self.model_version,
            "role": self.role,
            "party_id": self.party_id,
            "task_name": task_name,
            "component": component
        }
        self._create_entity(PipelineModelMeta, meta_info)

    def query(self, **kwargs):
        return self._query(PipelineModelMeta, model_id=self.model_id, model_version=self.model_version,
                           role=self.role, party_id=self.party_id, **kwargs)


class IOHandle:
    def read(self, model_id, model_version, role, party_id, task_name, model_name):
        ...

    def write(self, model_id, model_version, role, party_id, task_name, model_name, model_data):
        ...


class FileHandle(IOHandle):
    def write(self, model_id, model_version, role, party_id, task_name, model_name, model_file):
        base_path = os.path.join(MODEL_STORE_PATH, model_id, model_version, role, party_id, task_name)
        os.makedirs(base_path, exist_ok=True)
        model_file.save(os.path.join(base_path, model_name))

    def read(self, model_id, model_version, role, party_id, task_name, model_name):
        model_path = os.path.join(MODEL_STORE_PATH, model_id, model_version, role, party_id, task_name, model_name)
        return send_file(model_path, attachment_filename=model_name, as_attachment=True)
