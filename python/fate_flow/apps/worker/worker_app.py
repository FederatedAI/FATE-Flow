from webargs import fields

from fate_flow.controller.task_controller import TaskController
from fate_flow.entity.types import ReturnCode
from fate_flow.manager import model_manager
from fate_flow.manager.output_manager import OutputDataTracking
from fate_flow.operation.job_saver import JobSaver
from fate_flow.utils.api_utils import get_json_result, validate_request_json

page_name = 'worker'


@manager.route('/task/report', methods=['POST'])
@validate_request_json(status=fields.String(required=True), execution_id=fields.String(required=True),
                       error=fields.String(required=False))
def report_task(status, execution_id, error=None):
    tasks = JobSaver.query_task(execution_id=execution_id)
    if tasks:
        task = tasks[0]
        task_info = {
            "party_status": status,
            "job_id": task.f_job_id,
            "role": task.f_role,
            "party_id": task.f_party_id,
            "task_id": task.f_task_id,
            "task_version": task.f_task_version
        }
        TaskController.update_task_status(task_info=task_info)
        if error:
            task_info.update({"error_report": error})
            TaskController.update_task(task_info)
        return get_json_result()
    return get_json_result(code=ReturnCode.TASK.NO_FOUND, message="no found task")


@manager.route('/task/output/tracking', methods=['POST'])
@validate_request_json(execution_id=fields.String(required=True), meta_data=fields.Dict(required=True),
                       type=fields.String(required=True), uri=fields.String(required=True),
                       output_key=fields.String(required=True))
def log_output_artifacts(execution_id, meta_data, type, uri, output_key):
    tasks = JobSaver.query_task(execution_id=execution_id)
    if tasks:
        task = tasks[0]
        data_info = {
            "type": type,
            "uri": uri,
            "output_key": output_key,
            "meta": meta_data,
            "job_id": task.f_job_id,
            "role": task.f_role,
            "party_id": task.f_party_id,
            "task_id": task.f_task_id,
            "task_version": task.f_task_version,
            "task_name": task.f_task_name
        }
        OutputDataTracking.create(data_info)
        return get_json_result()
    return get_json_result(code=ReturnCode.TASK.NO_FOUND, message="no found task")


@manager.route('/task/model/<task_name>/<model_id>/<model_version>/<model_name>', methods=['POST'])
@validate_request_json(data=fields.Dict(required=True))
def save_output_model(task_name, model_id, model_version, model_name, data):
    model_manager.save_output_model(task_name, model_id, model_version, model_name, model_data=data)
    return get_json_result()


@manager.route('/task/model/<task_name>/<model_id>/<model_version>/<model_name>', methods=['GET'])
def get_output_model(task_name, model_id, model_version, model_name):
    data = model_manager.get_output_model(task_name, model_id, model_version, model_name)
    return get_json_result(data=data)
