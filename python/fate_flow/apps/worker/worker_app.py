from webargs import fields

from fate_flow.controller.task_controller import TaskController
from fate_flow.entity import RetCode
from fate_flow.entity.types import ReturnCode
from fate_flow.operation.job_saver import JobSaver
from fate_flow.utils.api_utils import get_json_result, validate_request_json

page_name = 'worker'


@manager.route('/task/report', methods=['POST'])
@validate_request_json(status=fields.String(required=True), execution_id=fields.String(required=True))
def report_task(status, execution_id):
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

        if not TaskController.update_task_status(task_info=task_info):
            return get_json_result(code=RetCode.NOT_EFFECTIVE, message="update job status does not take effect")
    return get_json_result(code=ReturnCode.TASK.NO_FOUND, message="no found task")


@manager.route('/task/output/artifacts/log', methods=['POST'])
@validate_request_json(execution_id=fields.String(required=True), key=fields.String(required=True),
                       value=fields.String(required=True), type=fields.String(required=True))
def log_output_artifacts():
    return get_json_result()
