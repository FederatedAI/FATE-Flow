from flask import request

from fate_flow.entity import JobConfigurationBase, RetCode
from fate_flow.operation.job_saver import JobSaver
from fate_flow.scheduler.dag_scheduler import DAGScheduler
from fate_flow.utils.api_utils import get_json_result

page_name = 'scheduler'


@manager.route('/job/create', methods=['POST'])
def create_job():
    submit_result = DAGScheduler.submit(JobConfigurationBase(**request.json))
    return get_json_result(retcode=submit_result["code"], retmsg=submit_result["message"],
                           job_id=submit_result["job_id"],
                           data=submit_result if submit_result["code"] == RetCode.SUCCESS else None)


@manager.route('/job/stop', methods=['POST'])
def stop_job():
    job_info = request.json
    retcode, retmsg = DAGScheduler.stop_job(job_id=job_info.get("job_id"),
                                            stop_status=job_info.get("stop_status"))
    return get_json_result(retcode=retcode, retmsg=retmsg)


@manager.route('/job/rerun', methods=['POST'])
def rerun_job():
    job_info = request.json
    DAGScheduler.set_job_rerun(job_id=job_info.get("job_id"), initiator_role=job_info.get("role"),
                               initiator_party_id=job_info.get("party_id"),
                               component_name=job_info.get("component_name"),
                               force=job_info.get("force", False),
                               auto=False)
    return get_json_result(retcode=0, retmsg='success')


@manager.route('/task/report', methods=['POST'])
def report_task():
    task_info = request.json
    JobSaver.update_task(task_info=task_info, is_scheduler=True)
    if task_info.get("party_status"):
        JobSaver.update_task_status(task_info, is_scheduler=True)
    return get_json_result(retcode=0, retmsg='success')
