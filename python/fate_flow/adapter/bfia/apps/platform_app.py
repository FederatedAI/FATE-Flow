from webargs import fields

from fate_flow.adapter.bfia.wheels.job import BfiaJobController
from fate_flow.adapter.bfia.utils.api_utils import BfiaAPI as API
from fate_flow.adapter.bfia.wheels.task import BfiaTaskController

page_name = 'platform'


# 发起方发起创建作业配置，并发送给己方调度层时调用的接口
@manager.route('/schedule/job/create_all', methods=['POST'])
@API.Input.json(flow_id=fields.String(required=False))
@API.Input.json(dag=fields.Dict(required=True))
@API.Input.json(config=fields.Dict(required=True))
@API.Input.json(old_job_id=fields.String(required=False))
def create_job(dag, config, flow_id="", old_job_id=""):
    job_id = BfiaJobController.request_create_job(dag, config, flow_id, old_job_id)
    return API.Output.json(data={"job_id": job_id})


# 发起方向己方调度层发起停止作业时调用的接口
@manager.route('/schedule/job/stop_all', methods=['POST'])
@API.Input.json(job_id=fields.String(required=True))
def stop_job(job_id):
    BfiaJobController.request_stop_job(job_id)
    return API.Output.json()


# 发起方向己方调度层发起停止任务时调用的接口
@manager.route('/schedule/job/stop_task', methods=['POST'])
@API.Input.json(job_id=fields.String(required=True))
@API.Input.json(task_name=fields.String(required=True))
def stop_task(job_id, task_name):
    BfiaTaskController.stop_local_task(job_id, task_name)
    return API.Output.json()


# 某个参与方向己方调度层发起查询作业列表时调用的接口
@manager.route('/schedule/job/query_job_list', methods=['GET'])
@API.Input.json(flow_id=fields.String(required=True))
def query_job_list(flow_id):
    job_list = BfiaJobController.query_job_status(flow_id=flow_id)
    return API.Output.json(job_list=job_list)


# 某个参与方向调度方发起查询作业状态时调用的接口
@manager.route('/schedule/job/status_all', methods=['GET'])
@API.Input.json(job_id=fields.String(required=True))
def get_job_status(job_id):
    status = BfiaTaskController.query_tasks_status(job_id)
    return API.Output.json(status=status)


# 某个参与方节点上层服务向调度层获取任务运行日志行数时调用的接口
@manager.route('/schedule/task/get_log_line', methods=['GET'])
@API.Input.json(task_id=fields.String(required=True))
@API.Input.json(log_level=fields.String(required=True))
def get_log_line(task_id, log_level):
    return API.Output.json(num=0)


# 某个参与方节点上层服务向调度层获取任务运行日志内容时调用的接口
@manager.route('/schedule/task/get_log', methods=['GET'])
@API.Input.json(task_id=fields.String(required=True))
@API.Input.json(log_level=fields.String(required=True))
@API.Input.json(start=fields.Int(required=True))
@API.Input.json(length=fields.Int(required=False))
def get_log(task_id, log_level, start, length=None):
    return API.Output.json(data=[])


# 某个参与方的算法组件层将任务运行的状态等回调信息推送给调度层时调用的接口
@manager.route('/schedule/task/callback', methods=['POST'])
@API.Input.json(task_id=fields.String(required=True))
@API.Input.json(status=fields.String(required=True))
@API.Input.json(role=fields.String(required=True))
def task_callback(task_id, status, role):
    role = role.split(".")[0]
    BfiaTaskController.callback_task(task_id, status, role)
    return API.Output.json()
