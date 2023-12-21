from webargs import fields

from fate_flow.adapter.bfia import apps
from fate_flow.adapter.bfia.scheduler import BfiaScheduler
from fate_flow.adapter.bfia.utils.api_utils import BfiaAPI as API
from fate_flow.adapter.bfia.utils.entity.code import ReturnCode
from fate_flow.adapter.bfia.wheels.job import BfiaJobController
from fate_flow.adapter.bfia.wheels.task import BfiaTaskController

page_name = 'interconn'


# scheduler
# 发起方向调度方发送创建作业请求时调用的接口
@manager.route('/schedule/job/create_all', methods=['POST'])
@API.Input.json(flow_id=fields.String(required=False))
@API.Input.json(job_id=fields.String(required=True))
@API.Input.json(dag=fields.Dict(required=True))
@API.Input.json(config=fields.Dict(required=True))
@API.Input.json(old_job_id=fields.String(required=False))
def create_job_all(job_id, dag, config, flow_id=None, old_job_id=None):
    dag_schema = dict(
        dag=dict(
            dag=dag,
            config=config,
            flow_id=flow_id,
            old_job_id=old_job_id
        ),
        schema_version=apps.__version__
    )
    submit_result = BfiaScheduler.create_all_job(job_id=job_id, dag=dag_schema)
    return API.Output.json(**submit_result)


# scheduler
# 发起方向调度方发送停止作业请求时调用的接口
@manager.route('/schedule/job/stop_all', methods=['POST'])
@API.Input.json(job_id=fields.String(required=True))
@API.Input.json(task_name=fields.String(required=False))
def stop_job_all(job_id, task_name=None):
    BfiaScheduler.stop_all_job(job_id=job_id, task_name=task_name)
    return API.Output.json()


# scheduler
# 某个参与方向调度方发起查询作业状态时调用的接口
@manager.route('/schedule/job/status_all', methods=['GET'])
@API.Input.json(job_id=fields.String(required=True))
def get_job_status_all(job_id):
    data = BfiaScheduler.query_job_status(job_id=job_id)
    return API.Output.json(data=data)


# scheduler
# 某个参与方向调度方或发起方作业审批结果时调用的接口
@manager.route('/schedule/job/audit_confirm', methods=['POST'])
@API.Input.json(job_id=fields.String(required=True))
@API.Input.json(status=fields.String(required=True))
def audit_confirm(job_id, status):
    status = BfiaScheduler.audit_confirm(job_id, status)
    if status:
        return API.Output.json()
    else:
        return API.Output.json(code=ReturnCode.FAILED)


# scheduler
# 任意参与方向发起方或调度方向推送任务回调信息时调用的接口
@manager.route('/schedule/task/callback', methods=['POST'])
@API.Input.json(task_id=fields.String(required=True))
@API.Input.json(role=fields.String(required=True))
@API.Input.json(status=fields.String(required=True))
@API.Input.headers(x_node_id=fields.String(required=True))
def callback_task(task_id, role, status, x_node_id):
    status = BfiaScheduler.callback_task(task_id, role, status, x_node_id)
    if status:
        return API.Output.json()
    return API.Output.json(code=ReturnCode.FAILED)


# partner
# 发起方或调度方向所有参与方发送创建作业请求时调用的接口
@manager.route('/schedule/job/create', methods=['POST'])
@API.Input.json(flow_id=fields.String(required=False))
@API.Input.json(job_id=fields.String(required=True))
@API.Input.json(dag=fields.Dict(required=True))
@API.Input.json(config=fields.Dict(required=True))
@API.Input.json(old_job_id=fields.String(required=False))
def create_job(job_id, dag, config, flow_id="", old_job_id=""):
    dag_schema = dict(
        dag=dict(
            dag=dag,
            config=config,
            flow_id=flow_id,
            old_job_id=old_job_id
        ),
        schema_version=apps.__version__
    )
    BfiaJobController.create_local_jobs(job_id=job_id, dag=dag_schema)
    return API.Output.json()


# partner
# 发起方或调度方向所有参与方发送启动作业请求时调用的接口，每个参与方只会被请求一次，当某个参与方包含多个角色时，
# 由参与方自己根据作业配置将不同角色的任务启动
@manager.route('/schedule/job/start', methods=['POST'])
@API.Input.json(job_id=fields.String(required=True))
def start_job(job_id):
    BfiaJobController.start_job(job_id=job_id)
    return API.Output.json()


# partner
# 发起方或调度方向所有参与方发送启动任务请求时调用的接口
@manager.route('/schedule/task/start', methods=['POST'])
@API.Input.json(job_id=fields.String(required=True))
@API.Input.json(task_id=fields.String(required=True))
@API.Input.json(task_name=fields.String(required=True))
def start_task(job_id, task_id, task_name):
    status = BfiaTaskController.start_tasks(job_id, task_id, task_name)
    if status:
        return API.Output.json()
    return API.Output.json(code=ReturnCode.FAILED)


# partner
# 发起方或调度方向所有参与方发送停止作业请求时调用的接口
@manager.route('/schedule/job/stop', methods=['POST'])
@API.Input.json(job_id=fields.String(required=True))
@API.Input.json(task_name=fields.String(required=False))
def stop_job(job_id, task_name=None):
    BfiaJobController.stop_local_jobs(job_id, task_name)
    return API.Output.json()


# partner
# 发起方或调度方向所有参与方查询任务回调信息时调用的接口
@manager.route('/schedule/task/poll', methods=['POST'])
@API.Input.json(task_id=fields.String(required=True))
@API.Input.json(role=fields.String(required=True))
def poll_task(task_id, role):
    status = BfiaTaskController.poll_task(task_id, role)
    return API.Output.json(data={"status": status})
