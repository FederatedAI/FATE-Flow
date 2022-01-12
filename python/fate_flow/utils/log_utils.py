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
import os
import typing
import traceback
import logging

from fate_arch.common.log import LoggerFactory, getLogger
from fate_flow.utils.base_utils import get_fate_flow_directory


def ready_log(msg, job=None, task=None, role=None, party_id=None, detail=None):
    prefix, suffix = base_msg(job, task, role, party_id, detail)
    return f"{prefix}{msg} ready{suffix}"


def start_log(msg, job=None, task=None, role=None, party_id=None, detail=None):
    prefix, suffix = base_msg(job, task, role, party_id, detail)
    return f"{prefix}start to {msg}{suffix}"


def successful_log(msg, job=None, task=None, role=None, party_id=None, detail=None):
    prefix, suffix = base_msg(job, task, role, party_id, detail)
    return f"{prefix}{msg} successfully{suffix}"


def warning_log(msg, job=None, task=None, role=None, party_id=None, detail=None):
    prefix, suffix = base_msg(job, task, role, party_id, detail)
    return f"{prefix}{msg} is not effective{suffix}"


def failed_log(msg, job=None, task=None, role=None, party_id=None, detail=None):
    prefix, suffix = base_msg(job, task, role, party_id, detail)
    return f"{prefix}failed to {msg}{suffix}"


def base_msg(job=None, task=None, role: str = None, party_id: typing.Union[str, int] = None, detail=None):
    if detail:
        detail_msg = f" detail: \n{detail}"
    else:
        detail_msg = ""
    if task is not None:
        return f"task {task.f_task_id} {task.f_task_version} ", f" on {task.f_role} {task.f_party_id}{detail_msg}"
    elif job is not None:
        return "", f" on {job.f_role} {job.f_party_id}{detail_msg}"
    elif role and party_id:
        return "", f" on {role} {party_id}{detail_msg}"
    else:
        return "", f"{detail_msg}"


def exception_to_trace_string(ex):
    return "".join(traceback.TracebackException.from_exception(ex).format())


def get_logger_base_dir():
    job_log_dir = get_fate_flow_directory('logs')
    return job_log_dir


def get_job_logger(job_id, log_type):
    fate_flow_log_dir = get_fate_flow_directory('logs', 'fate_flow')
    job_log_dir = get_fate_flow_directory('logs', job_id)
    if not job_id:
        log_dirs = [fate_flow_log_dir]
    else:
        if log_type == 'audit':
            log_dirs = [job_log_dir, fate_flow_log_dir]
        else:
            log_dirs = [job_log_dir]
    if LoggerFactory.log_share:
        oldmask = os.umask(000)
        os.makedirs(job_log_dir, exist_ok=True)
        os.makedirs(fate_flow_log_dir, exist_ok=True)
        os.umask(oldmask)
    else:
        os.makedirs(job_log_dir, exist_ok=True)
        os.makedirs(fate_flow_log_dir, exist_ok=True)
    logger = LoggerFactory.new_logger(f"{job_id}_{log_type}")
    for job_log_dir in log_dirs:
        handler = LoggerFactory.get_handler(class_name=None, level=LoggerFactory.LEVEL,
                                            log_dir=job_log_dir, log_type=log_type, job_id=job_id)
        error_handler = LoggerFactory.get_handler(class_name=None, level=logging.ERROR, log_dir=job_log_dir, log_type=log_type, job_id=job_id)
        logger.addHandler(handler)
        logger.addHandler(error_handler)
    with LoggerFactory.lock:
        LoggerFactory.schedule_logger_dict[job_id + log_type] = logger
    return logger


def schedule_logger(job_id=None, delete=False):
    if not job_id:
        return getLogger("fate_flow_schedule")
    else:
        if delete:
            with LoggerFactory.lock:
                try:
                    for key in LoggerFactory.schedule_logger_dict.keys():
                        if job_id in key:
                            del LoggerFactory.schedule_logger_dict[key]
                except:
                    pass
            return True
        key = job_id + 'schedule'
        if key in LoggerFactory.schedule_logger_dict:
            return LoggerFactory.schedule_logger_dict[key]
        return get_job_logger(job_id, "schedule")


def audit_logger(job_id='', log_type='audit'):
    key = job_id + log_type
    if key in LoggerFactory.schedule_logger_dict.keys():
        return LoggerFactory.schedule_logger_dict[key]
    return get_job_logger(job_id=job_id, log_type=log_type)


def sql_logger(job_id='', log_type='sql'):
    key = job_id + log_type
    if key in LoggerFactory.schedule_logger_dict.keys():
        return LoggerFactory.schedule_logger_dict[key]
    return get_job_logger(job_id=job_id, log_type=log_type)


def detect_logger(job_id='', log_type='detect'):
    key = job_id + log_type
    if key in LoggerFactory.schedule_logger_dict.keys():
        return LoggerFactory.schedule_logger_dict[key]
    return get_job_logger(job_id=job_id, log_type=log_type)