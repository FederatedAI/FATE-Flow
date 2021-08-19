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
import os
import subprocess
import psutil
from fate_arch.common.log import schedule_logger
from fate_flow.db.db_models import Task
from fate_flow.entity.types import KillProcessRetCode
from fate_flow.settings import SUBPROCESS_STD_LOG_NAME
from fate_flow.settings import stat_logger


def run_subprocess(job_id, config_dir, process_cmd, extra_env: dict = None, log_dir=None, cwd_dir=None):
    logger = schedule_logger(job_id) if job_id else stat_logger
    process_cmd = [str(cmd) for cmd in process_cmd]
    logger.info('start process command: {}'.format(' '.join(process_cmd)))

    os.makedirs(config_dir, exist_ok=True)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
    std_log = open(os.path.join(log_dir if log_dir else config_dir, SUBPROCESS_STD_LOG_NAME), 'w')
    pid_path = os.path.join(config_dir, 'pid')

    if os.name == 'nt':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
    else:
        startupinfo = None
    subprocess_env = None
    if extra_env:
        subprocess_env = os.environ.copy()
        for name, value in extra_env.items():
            if name.endswith("PATH"):
                subprocess_env[name] = subprocess_env.get(name, "") + f":{value}"
            else:
                subprocess_env[name] = value
    p = subprocess.Popen(process_cmd,
                         stdout=std_log,
                         stderr=std_log,
                         startupinfo=startupinfo,
                         cwd=cwd_dir,
                         env=subprocess_env
                         )
    with open(pid_path, 'w') as f:
        f.truncate()
        f.write(str(p.pid) + "\n")
        f.flush()
    logger.info('start process command: {} successfully, pid is {}'.format(' '.join(process_cmd), p.pid))
    return p


def check_job_process(pid):
    if pid < 0:
        return False
    if pid == 0:
        raise ValueError('invalid PID 0')
    try:
        os.kill(pid, 0)
    except OSError as err:
        if err.errno == errno.ESRCH:
            # ESRCH == No such process
            return False
        elif err.errno == errno.EPERM:
            # EPERM clearly means there's a process to deny access to
            return True
        else:
            # According to "man 2 kill" possible error values are
            # (EINVAL, EPERM, ESRCH)
            raise
    else:
        return True


def check_process_by_keyword(keywords):
    if not keywords:
        return True
    keyword_filter_cmd = ' |'.join(['grep %s' % keyword for keyword in keywords])
    ret = os.system('ps aux | {} | grep -v grep | grep -v "ps aux "'.format(keyword_filter_cmd))
    return ret == 0


def get_subprocess_std(log_dir):
    with open(os.path.join(log_dir, SUBPROCESS_STD_LOG_NAME), "r") as fr:
        text = fr.read()
    return text


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
    # Todo: The same map should be used for run task command
    run_cmd_map = {
        3: "f_job_id",
        5: "f_component_name",
        7: "f_task_id",
        9: "f_task_version",
        11: "f_role",
        13: "f_party_id"
    }
    try:
        cmdline = process.cmdline()
        schedule_logger(task.f_job_id).info(cmdline)
    except Exception as e:
        # Not sure whether the process is a task executor process, operations processing is required
        schedule_logger(task.f_job_id).warning(e)
        return False
    for i, k in run_cmd_map.items():
        if len(cmdline) > i and cmdline[i] == str(getattr(task, k)):
            continue
        else:
            # todo: The logging level should be obtained first
            if len(cmdline) > i:
                schedule_logger(task.f_job_id).debug(f"cmd map {i} {k}, cmd value {cmdline[i]} task value {getattr(task, k)}")
            return False
    else:
        return True


def kill_task_executor_process(task: Task, only_child=False):
    try:
        if not task.f_run_pid:
            schedule_logger(task.f_job_id).info("job {} task {} {} {} with {} party status no process pid".format(
                task.f_job_id, task.f_task_id, task.f_role, task.f_party_id, task.f_party_status))
            return KillProcessRetCode.NOT_FOUND
        pid = int(task.f_run_pid)
        schedule_logger(task.f_job_id).info("try to stop job {} task {} {} {} with {} party status process pid:{}".format(
            task.f_job_id, task.f_task_id, task.f_role, task.f_party_id, task.f_party_status, pid))
        if not check_job_process(pid):
            schedule_logger(task.f_job_id).info("can not found job {} task {} {} {} with {} party status process pid:{}".format(
                task.f_job_id, task.f_task_id, task.f_role, task.f_party_id, task.f_party_status, pid))
            return KillProcessRetCode.NOT_FOUND
        p = psutil.Process(int(pid))
        if not is_task_executor_process(task=task, process=p):
            schedule_logger(task.f_job_id).warning("this pid {} is not job {} task {} {} {} executor".format(
                pid, task.f_job_id, task.f_task_id, task.f_role, task.f_party_id))
            return KillProcessRetCode.ERROR_PID
        for child in p.children(recursive=True):
            if check_job_process(child.pid) and is_task_executor_process(task=task, process=child):
                child.kill()
        if not only_child:
            if check_job_process(p.pid) and is_task_executor_process(task=task, process=p):
                p.kill()
        schedule_logger(task.f_job_id).info("successfully stop job {} task {} {} {} process pid:{}".format(
            task.f_job_id, task.f_task_id, task.f_role, task.f_party_id, pid))
        return KillProcessRetCode.KILLED
    except Exception as e:
        raise e
