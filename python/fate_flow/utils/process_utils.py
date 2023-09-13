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
import errno
import json
import os
import subprocess
import time

import psutil

from fate_flow.entity.code import KillProcessRetCode
from fate_flow.utils.log import getLogger
from fate_flow.utils.log_utils import schedule_logger
from fate_flow.db.db_models import Task
from fate_flow.entity.types import ProcessRole

stat_logger = getLogger()


def run_subprocess(
        job_id, config_dir, process_cmd, process_name, added_env: dict = None, std_dir=None, cwd_dir=None, stderr=None
):
    logger = schedule_logger(job_id) if job_id else stat_logger
    process_cmd = [str(cmd) for cmd in process_cmd]
    logger.info("start process command: \n{}".format(" ".join(process_cmd)))

    os.makedirs(config_dir, exist_ok=True)
    os.makedirs(std_dir, exist_ok=True)
    if not std_dir:
        std_dir = config_dir
    std_path = get_std_path(std_dir=std_dir, process_name=process_name)

    std = open(std_path, 'w')
    if not stderr:
        stderr = std
    pid_path = os.path.join(config_dir, "pid", f"{process_name}")
    os.makedirs(os.path.dirname(pid_path), exist_ok=True)

    if os.name == 'nt':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
    else:
        startupinfo = None

    subprocess_env = os.environ.copy()
    subprocess_env["PROCESS_ROLE"] = ProcessRole.WORKER.value
    if added_env:
        for name, value in added_env.items():
            if not value:
                continue
            if name.endswith("PATH") and subprocess_env.get(name) is not None:
                value += ':' + subprocess_env[name]
            subprocess_env[name] = value
    logger.info(f"RUN ENV：{json.dumps(subprocess_env)}")
    p = subprocess.Popen(process_cmd,
                         stdout=std,
                         stderr=stderr,
                         startupinfo=startupinfo,
                         cwd=cwd_dir,
                         env=subprocess_env
                         )
    with open(pid_path, 'w') as f:
        f.truncate()
        f.write(str(p.pid) + "\n")
        f.flush()
    logger.info(f"start process successfully, pid: {p.pid}, std log path: {std_path}")
    return p


def check_process(pid, task: Task = None, expected_cmdline: list = None):
    if pid < 0:
        return False
    if pid == 0:
        raise ValueError('invalid PID 0')
    try:
        os.kill(pid, 0)
    except OSError as err:
        if err.errno == errno.ESRCH:
            # ESRCH == No such process
            ret = False
        elif err.errno == errno.EPERM:
            # EPERM clearly means there's a process to deny access to
            ret = True
        else:
            # According to "man 2 kill" possible error values are
            # (EINVAL, EPERM, ESRCH)
            raise
    else:
        ret = True
    if ret and task is not None:
        p = get_process_instance(pid)
        if p:
            return True
        else:
            return False
    elif ret and expected_cmdline is not None:
        p = get_process_instance(pid)
        try:
            return check_process_by_cmdline(actual=p.cmdline(), expected=expected_cmdline)
        except psutil.NoSuchProcess:
            stat_logger.warning(f"no such process {pid}")
            return False
    else:
        return ret


def check_process_by_keyword(keywords):
    if not keywords:
        return True
    keyword_filter_cmd = ' |'.join(['grep %s' % keyword for keyword in keywords])
    ret = os.system('ps aux | {} | grep -v grep | grep -v "ps aux "'.format(keyword_filter_cmd))
    return ret == 0


def check_process_by_cmdline(actual: list, expected: list):
    if len(actual) != len(expected):
        return False
    for i, v in enumerate(actual):
        if str(v) != str(expected[i]):
            return False
    else:
        return True


def get_std_path(std_dir, process_name):
    return os.path.join(std_dir, process_name)


def wait_child_process(signum, frame):
    try:
        while True:
            child_pid, status = os.waitpid(-1, os.WNOHANG)
            if child_pid == 0:
                stat_logger.info('no child process was immediately available')
                break
            exitcode = status >> 8
            stat_logger.info(f'child process {child_pid} exit with exitcode {exitcode}')
    except OSError as e:
        if e.errno == errno.ECHILD:
            stat_logger.info('current process has no existing unwaited-for child processes.')
        else:
            raise


def is_task_executor_process(task: Task, process: psutil.Process):
    """
    check the process if task executor or not by command
    :param task:
    :param process:
    :return:
    """
    try:
        cmdline = process.cmdline()
    except Exception as e:
        # Not sure whether the process is a task executor process, operations processing is required
        schedule_logger(task.f_job_id).warning(e)
        return False
    else:
        schedule_logger(task.f_job_id).info(cmdline)

    if task.f_worker_id and task.f_worker_id in cmdline:
        return True

    if len(cmdline) != len(task.f_cmd):
        return False

    for i, v in enumerate(task.f_cmd):
        if cmdline[i] != str(v):
            return False

    return True


def kill_task_executor_process(task: Task, only_child=False):
    try:
        if not task.f_run_pid:
            schedule_logger(task.f_job_id).info("task {} {} {} with {} party status no process pid".format(
                task.f_task_id, task.f_role, task.f_party_id, task.f_party_status))
            return KillProcessRetCode.NOT_FOUND
        pid = int(task.f_run_pid)
        schedule_logger(task.f_job_id).info("try to stop task {} {} {} with {} party status process pid:{}".format(
            task.f_task_id, task.f_role, task.f_party_id, task.f_party_status, pid))
        if not check_process(pid):
            schedule_logger(task.f_job_id).info("can not found task {} {} {} with {} party status process pid:{}".format(
                task.f_task_id, task.f_role, task.f_party_id, task.f_party_status, pid))
            return KillProcessRetCode.NOT_FOUND
        p = get_process_instance(pid)
        if p is None:
            return KillProcessRetCode.NOT_FOUND
        if not is_task_executor_process(task=task, process=p):
            schedule_logger(task.f_job_id).warning("this pid {} is not task {} {} {} executor".format(
                pid, task.f_task_id, task.f_role, task.f_party_id))
            return KillProcessRetCode.ERROR_PID
        for child in p.children(recursive=True):
            if check_process(pid=child.pid, task=task):
                child.kill()
        if not only_child:
            if check_process(pid, task=task):
                p.kill()
        schedule_logger(task.f_job_id).info("successfully stop task {} {} {} process pid:{}".format(
            task.f_task_id, task.f_role, task.f_party_id, pid))
        return KillProcessRetCode.KILLED
    except Exception as e:
        raise e


def kill(p, wait_before_terminate=10, wait_before_kill=10):
    # wait and check
    for _ in range(wait_before_terminate):
        if p.is_running():
            time.sleep(1)
        else:
            break
    try:
        # send sigterm, gracefully stop
        if p.is_running():
            p.terminate()
    except:
        pass
    finally:
        # gracefully stop may takes few seconds, wati and check again
        for _ in range(wait_before_kill):
            if p.is_running():
                time.sleep(1)
            else:
                break
        try:
            # nothing could do now, kill anyway
            if p.is_running():
                p.kill()
        except:
            pass


def kill_process(process: psutil.Process = None, pid: int = None, expected_cmdline: list = None):
    process = process if process is not None else get_process_instance(pid)
    if process is None:
        return
    for child in process.children(recursive=True):
        try:
            if check_process(pid=child.pid):
                child.kill()
        except Exception as e:
            stat_logger.warning(f"kill {child.pid} process failed", exc_info=True)
    if check_process(pid=process.pid, expected_cmdline=expected_cmdline):
        process.kill()


def get_process_instance(pid: int):
    try:
        return psutil.Process(int(pid))
    except psutil.NoSuchProcess:
        stat_logger.warning(f"no such process {pid}")
        return
    except Exception as e:
        raise e
