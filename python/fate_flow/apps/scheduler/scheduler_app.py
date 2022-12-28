from webargs import fields

from fate_flow.hub.parser.default import DAGSchema
from fate_flow.operation.job_saver import ScheduleJobSaver
from fate_flow.scheduler.job_scheduler import DAGScheduler
from fate_flow.utils.api_utils import get_json_result, validate_request_json, task_request_json

page_name = 'scheduler'


@manager.route('/job/create', methods=['POST'])
@validate_request_json(dag_schema=fields.Dict(required=True))
def create_job(dag_schema):
    submit_result = DAGScheduler.submit(DAGSchema(**dag_schema))
    return get_json_result(**submit_result)


@manager.route('/task/report', methods=['POST'])
@task_request_json(status=fields.String(required=False))
def report_task(job_id, role, party_id, task_id, task_version, status=None):
    ScheduleJobSaver.update_task_status(task_info={
        "job_id": job_id,
        "role": role,
        "party_id": party_id,
        "task_id": task_id,
        "task_version": task_version,
        "status": status
    })
    return get_json_result(code=0, message='success')


@manager.route('/job/stop', methods=['POST'])
@validate_request_json(job_id=fields.String(required=True), stop_status=fields.String(required=False))
def stop_job(job_id, stop_status=None):
    retcode, retmsg = DAGScheduler.stop_job(job_id=job_id,
                                            stop_status=stop_status)
    return get_json_result(code=retcode, message=retmsg)


@manager.route('/job/rerun', methods=['POST'])
@validate_request_json(job_id=fields.String(required=True))
def rerun_job(job_id):
    DAGScheduler.set_job_rerun(job_id=job_id, auto=False)
    return get_json_result()
