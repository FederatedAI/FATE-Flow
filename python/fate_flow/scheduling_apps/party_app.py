#
#  Copyright 2019 The FATE Authors. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
from flask import request

from fate_flow.controller.job_controller import JobController
from fate_flow.controller.task_controller import TaskController
from fate_flow.db.runtime_config import RuntimeConfig
from fate_flow.entity import RetCode
from fate_flow.entity.types import TaskCleanResourceType
from fate_flow.manager.dependence_manager import DependenceManager
from fate_flow.manager.resource_manager import ResourceManager
from fate_flow.operation.job_saver import JobSaver
from fate_flow.utils.api_utils import get_json_result
from fate_flow.utils.authentication_utils import request_authority_certification
from fate_flow.utils.model_utils import compare_version


# execute command on every party
@manager.route('/<job_id>/<role>/<party_id>/create', methods=['POST'])
@request_authority_certification(party_id_index=-2, role_index=-3, command='create')
def create_job(job_id, role, party_id):
    src_fate_ver = request.json.get('src_fate_ver')
    if src_fate_ver is not None and compare_version(src_fate_ver, '1.7.0') == 'lt':
        return get_json_result(retcode=RetCode.INCOMPATIBLE_FATE_VER, retmsg='Incompatible FATE versions',
                               data={'src_fate_ver': src_fate_ver, "current_fate_ver": RuntimeConfig.get_env('FATE')})

    try:
        result = JobController.create_job(job_id=job_id, role=role, party_id=int(party_id), job_info=request.json)
        return get_json_result(retcode=0, retmsg='success', data=result)
    except RuntimeError as e:
        return get_json_result(retcode=RetCode.OPERATING_ERROR, retmsg=str(e), data={"job_id": job_id})


@manager.route('/<job_id>/<role>/<party_id>/component/inheritance/check', methods=['POST'])
def component_inheritance_check(job_id, role, party_id):
    job = JobSaver.query_job(job_id=job_id, role=role, party_id=party_id)[0]
    component_list = DependenceManager.component_check(job, check_type="inheritance")
    return get_json_result(data=component_list)


@manager.route('/<job_id>/<role>/<party_id>/component/rerun/check', methods=['POST'])
def component_rerun_check(job_id, role, party_id):
    job = JobSaver.query_job(job_id=job_id, role=role, party_id=party_id)[0]
    component_list = DependenceManager.component_check(job, check_type="rerun")
    return get_json_result(data=component_list)


@manager.route('/<job_id>/<role>/<party_id>/dependence/check', methods=['POST'])
def check_dependence(job_id, role, party_id):
    job = JobSaver.query_job(job_id=job_id, role=role, party_id=party_id)[0]
    status = DependenceManager.check_job_dependence(job)
    if status:
        return get_json_result(retcode=0, retmsg='success')
    else:
        return get_json_result(retcode=RetCode.RUNNING,
                               retmsg=f"check for job {job_id} dependence failed, "
                                      f"dependencies are being installed automatically, it may take a few minutes")


@manager.route('/<job_id>/<role>/<party_id>/resource/apply', methods=['POST'])
def apply_resource(job_id, role, party_id):
    status = ResourceManager.apply_for_job_resource(job_id=job_id, role=role, party_id=int(party_id))
    if status:
        return get_json_result(retcode=0, retmsg='success')
    else:
        return get_json_result(retcode=RetCode.OPERATING_ERROR, retmsg=f"apply for job {job_id} resource failed")


@manager.route('/<job_id>/<role>/<party_id>/resource/return', methods=['POST'])
def return_resource(job_id, role, party_id):
    status = ResourceManager.return_job_resource(job_id=job_id, role=role, party_id=int(party_id))
    if status:
        return get_json_result(retcode=0, retmsg='success')
    else:
        return get_json_result(retcode=RetCode.OPERATING_ERROR, retmsg=f"apply for job {job_id} resource failed")


@manager.route('/<job_id>/<role>/<party_id>/start', methods=['POST'])
def start_job(job_id, role, party_id):
    JobController.start_job(job_id=job_id, role=role, party_id=int(party_id), extra_info=request.json)
    return get_json_result(retcode=0, retmsg='success')


@manager.route('/<job_id>/<role>/<party_id>/align', methods=['POST'])
def align_job_args(job_id, role, party_id):
    JobController.align_job_args(job_info=request.json, role=role, party_id=party_id, job_id=job_id)
    return get_json_result(retcode=0, retmsg='success')


@manager.route('/<job_id>/<role>/<party_id>/update', methods=['POST'])
def update_job(job_id, role, party_id):
    job_info = {}
    job_info.update(request.json)
    job_info.update({
        "job_id": job_id,
        "role": role,
        "party_id": party_id
    })
    JobController.update_job(job_info=job_info)
    return get_json_result(retcode=0, retmsg='success')


@manager.route('/<job_id>/<role>/<party_id>/parameter/update', methods=['POST'])
def update_parameters(job_id, role, party_id):
    JobController.update_parameter(job_id=job_id, role=role, party_id=party_id, updated_parameters=request.json)
    return get_json_result(retcode=0, retmsg='success')


@manager.route('/<job_id>/<role>/<party_id>/status/<status>', methods=['POST'])
def job_status(job_id, role, party_id, status):
    job_info = request.json
    # some value of job_info is initiator, should be updated
    job_info.update({
        "job_id": job_id,
        "role": role,
        "party_id": party_id,
        "status": status
    })
    if JobController.update_job_status(job_info=job_info):
        return get_json_result(retcode=0, retmsg='success')
    else:
        return get_json_result(retcode=RetCode.NOT_EFFECTIVE, retmsg="update job status does not take effect")


@manager.route('/<job_id>/<role>/<party_id>/model', methods=['POST'])
def save_pipelined_model(job_id, role, party_id):
    JobController.save_pipelined_model(job_id=job_id, role=role, party_id=party_id)
    return get_json_result(retcode=0, retmsg='success')


@manager.route('/<job_id>/<role>/<party_id>/stop/<stop_status>', methods=['POST'])
def stop_job(job_id, role, party_id, stop_status):
    kill_status, kill_details = JobController.stop_jobs(job_id=job_id, stop_status=stop_status, role=role, party_id=party_id)
    return get_json_result(retcode=RetCode.SUCCESS if kill_status else RetCode.EXCEPTION_ERROR,
                           retmsg='success' if kill_status else 'failed',
                           data=kill_details)


@manager.route('/<job_id>/<role>/<party_id>/clean', methods=['POST'])
def clean(job_id, role, party_id):
    JobController.clean_job(job_id=job_id, role=role, party_id=party_id, roles=request.json)
    return get_json_result(retcode=0, retmsg='success')


# Control API for task
@manager.route('/<job_id>/<component_name>/<task_id>/<task_version>/<role>/<party_id>/create', methods=['POST'])
def create_task(job_id, component_name, task_id, task_version, role, party_id):
    JobController.initialize_task(role, party_id, request.json)
    return get_json_result(retcode=0, retmsg='success')


@manager.route('/<job_id>/<component_name>/<task_id>/<task_version>/<role>/<party_id>/start', methods=['POST'])
@request_authority_certification(party_id_index=-2, role_index=-3, command='run')
def start_task(job_id, component_name, task_id, task_version, role, party_id):
    TaskController.start_task(job_id, component_name, task_id, task_version, role, party_id, **request.json)
    return get_json_result(retcode=0, retmsg='success')


@manager.route('/<job_id>/<component_name>/<task_id>/<task_version>/<role>/<party_id>/report', methods=['POST'])
def report_task(job_id, component_name, task_id, task_version, role, party_id):
    task_info = {}
    task_info.update(request.json)
    task_info.update({
        "job_id": job_id,
        "task_id": task_id,
        "task_version": task_version,
        "role": role,
        "party_id": party_id,
    })
    TaskController.update_task(task_info=task_info)
    if task_info.get("party_status"):
        if not TaskController.update_task_status(task_info=task_info):
            return get_json_result(retcode=RetCode.NOT_EFFECTIVE, retmsg="update job status does not take effect")
    return get_json_result(retcode=0, retmsg='success')


@manager.route('/<job_id>/<component_name>/<task_id>/<task_version>/<role>/<party_id>/update', methods=['POST'])
def update_task(job_id, component_name, task_id, task_version, role, party_id):
    task_info = {}
    task_info.update(request.json)
    task_info.update({
        "job_id": job_id,
        "task_id": task_id,
        "task_version": task_version,
        "role": role,
        "party_id": party_id,
    })
    TaskController.update_task(task_info=task_info)
    return get_json_result(retcode=0, retmsg='success')


@manager.route('/<job_id>/<component_name>/<task_id>/<task_version>/<role>/<party_id>/collect', methods=['POST'])
def collect_task(job_id, component_name, task_id, task_version, role, party_id):
    task_info = TaskController.collect_task(job_id=job_id, component_name=component_name, task_id=task_id, task_version=task_version, role=role, party_id=party_id)
    if task_info:
        return get_json_result(retcode=RetCode.SUCCESS, retmsg="success", data=task_info)
    else:
        return get_json_result(retcode=RetCode.OPERATING_ERROR, retmsg="query task failed")


@manager.route('/<job_id>/<component_name>/<task_id>/<task_version>/<role>/<party_id>/status/<status>', methods=['POST'])
def task_status(job_id, component_name, task_id, task_version, role, party_id, status):
    task_info = {}
    task_info.update({
        "job_id": job_id,
        "task_id": task_id,
        "task_version": task_version,
        "role": role,
        "party_id": party_id,
        "status": status
    })
    if TaskController.update_task_status(task_info=task_info):
        return get_json_result(retcode=0, retmsg='success')
    else:
        return get_json_result(retcode=RetCode.NOT_EFFECTIVE, retmsg="update job status does not take effect")


@manager.route('/<job_id>/<component_name>/<task_id>/<task_version>/<role>/<party_id>/stop/<stop_status>', methods=['POST'])
@request_authority_certification(party_id_index=-3, role_index=-4, command='stop')
def stop_task(job_id, component_name, task_id, task_version, role, party_id, stop_status):
    tasks = JobSaver.query_task(job_id=job_id, task_id=task_id, task_version=task_version, role=role, party_id=int(party_id))
    kill_status = True
    for task in tasks:
        kill_status = kill_status & TaskController.stop_task(task=task, stop_status=stop_status)
    return get_json_result(retcode=RetCode.SUCCESS if kill_status else RetCode.EXCEPTION_ERROR,
                           retmsg='success' if kill_status else 'failed')


@manager.route('/<job_id>/<component_name>/<task_id>/<task_version>/<role>/<party_id>/clean/<content_type>', methods=['POST'])
def clean_task(job_id, component_name, task_id, task_version, role, party_id, content_type):
    TaskController.clean_task(job_id=job_id, task_id=task_id, task_version=task_version, role=role, party_id=int(party_id), content_type=TaskCleanResourceType(content_type))
    return get_json_result(retcode=0, retmsg='success')


