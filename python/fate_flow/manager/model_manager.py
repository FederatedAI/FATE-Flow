import json
import os.path

from fate_flow.settings import MODEL_STORE_PATH


def save_output_model(task_name, model_id, model_version, model_name, model_data):
    base_path = os.path.join(MODEL_STORE_PATH, model_id, model_version, task_name)
    os.makedirs(base_path, exist_ok=True)
    with open(os.path.join(base_path, model_name), "w") as fw:
        json.dump(model_data, fw)


def get_output_model(task_name, model_id, model_version, model_name):
    base_path = os.path.join(MODEL_STORE_PATH, model_id, model_version, task_name, model_name)
    with open(base_path, "r") as fr:
        return json.load(fr)
