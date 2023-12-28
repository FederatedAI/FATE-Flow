import os
import subprocess

from fate_flow.runtime.system_settings import LOG_DIR
from fate_flow.utils.log_utils import replace_ip

JOB = ["schedule_info", "schedule_error"]
TASK = ["task_error", "task_info", "task_warning", "task_debug"]


def parameters_check(log_type, job_id, role, party_id):
    if log_type in JOB:
        if not job_id:
            return False
    if log_type in TASK:
        if not job_id or not role or not party_id:
            return False
    return True


class LogManager:
    def __init__(self, log_type, job_id, party_id="", role="", task_name="", **kwargs):
        self.log_type = log_type
        self.job_id = job_id
        self.party_id = party_id
        self.role = role
        self.task_name = task_name

    @property
    def task_base_path(self):
        if self.role and self.party_id:
            path = os.path.join(self.job_id, self.role, self.party_id)
            if self.task_name:
                path = os.path.join(path, self.task_name, 'root')
            return path
        return ""

    @property
    def file_path(self):
        status = parameters_check(self.log_type, self.job_id, self.role, self.party_id)
        if not status:
            raise Exception(f"job type {self.log_type} Missing parameters")
        type_dict = {
            "schedule_info": os.path.join(self.job_id, "fate_flow_schedule.log"),
            "schedule_error": os.path.join(self.job_id, "fate_flow_schedule_error.log"),
            "task_error": os.path.join(self.task_base_path, "ERROR"),
            "task_warning": os.path.join(self.task_base_path, "WARNING"),
            "task_info": os.path.join(self.task_base_path, "INFO"),
            "task_debug": os.path.join(self.task_base_path, "DEBUG")
        }
        if self.log_type not in type_dict.keys():
            raise Exception(f"no found log type {self.log_type}")
        return os.path.join(LOG_DIR, type_dict[self.log_type])

    def cat_log(self, begin, end):
        line_list = []
        log_path = self.file_path
        if begin and end:
            cmd = f"cat {log_path} | tail -n +{begin}| head -n {end-begin+1}"
        elif begin:
            cmd = f"cat {log_path} | tail -n +{begin}"
        elif end:
            cmd = f"cat {log_path} | head -n {end}"
        else:
            cmd = f"cat {log_path}"
        lines = self.execute(cmd)
        if lines:
            line_list = []
            line_num = begin if begin else 1
            for line in lines.split("\n"):
                line = replace_ip(line)
                line_list.append({"line_num": line_num, "content": line})
                line_num += 1
        return line_list

    def count(self):
        try:
            if os.path.exists(self.file_path):
                return int(self.execute(f"cat {self.file_path} | wc -l").strip())
            return 0
        except:
            return 0

    @staticmethod
    def execute(cmd):
        res = subprocess.run(
            cmd, shell=True, universal_newlines=True,
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        )
        return res.stdout
