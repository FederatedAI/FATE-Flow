from webargs import fields

from fate_flow.utils.api_utils import API

page_name = 'platform'


@manager.route('/schedule/job/create_all', methods=['POST'])
@API.Input.json(flow_id=fields.String(required=False))
@API.Input.json(dag=fields.Dict(required=True))
@API.Input.json(config=fields.Dict(required=True))
@API.Input.json(old_job_id=fields.String(required=False))
def create_job(dag, config, flow_id=None, old_job_id=None):
    return API.Output.json(job_id="")


@manager.route('/schedule/job/stop_all', methods=['POST'])
@API.Input.json(job_id=fields.String(required=True))
def stop_job(job_id):
    return API.Output.json()


@manager.route('/schedule/job/stop_task', methods=['POST'])
@API.Input.json(job_id=fields.String(required=True))
@API.Input.json(task_name=fields.String(required=True))
def stop_task(job_id, task_name):
    return API.Output.json()


# options
@manager.route('/schedule/job/query_job_list', methods=['POST'])
@API.Input.json(flow_id=fields.String(required=True))
def query_job_list(flow_id):
    return API.Output.json(job_list=[{}])


@manager.route('/schedule/job/status_all', methods=['GET'])
@API.Input.params(job_id=fields.String(required=True))
def get_job_status(job_id):
    return API.Output.json(status=[{}])


@manager.route('/schedule/task/get_log_line', methods=['GET'])
@API.Input.params(task_id=fields.String(required=True))
@API.Input.params(log_level=fields.String(required=True))
def get_log_line(task_id, log_level):
    return API.Output.json(num=0)


@manager.route('/schedule/task/get_log', methods=['GET'])
@API.Input.params(task_id=fields.String(required=True))
@API.Input.params(log_level=fields.String(required=True))
@API.Input.params(start=fields.Int(required=True))
@API.Input.params(length=fields.Int(required=False))
def get_log(task_id, log_level, start, length=None):
    return API.Output.json(data=[])


@manager.route('/schedule/task/callback', methods=['POST'])
@API.Input.json(task_id=fields.String(required=True))
@API.Input.json(status=fields.String(required=True))
@API.Input.json(role=fields.String(required=True))
def task_callback(task_id, status, role):
    return API.Output.json()
