import os
import re

from fate_flow.utils.base_utils import get_fate_flow_directory

JOB = ["jobSchedule", "jobScheduleError"]
PARTY = ["partyError", "partyWarning", "partyInfo", "partyDebug"]
COMPONENT = ["componentInfo"]
LOGMapping = {
    "jobSchedule": "fate_flow_schedule.log",
    "jobScheduleError": "fate_flow_schedule_error.log",
    "partyError": "ERROR.log",
    "partyWarning": "WARNING.log",
    "partyInfo": "INFO.log",
    "partyDebug": "DEBUG.log",
    "componentInfo": "INFO.log"
}

def parameters_check(log_type, job_id, role, party_id, component_name):
    if log_type in JOB:
        if not job_id:
            return False
    if log_type in PARTY:
        if not job_id or not role or not party_id:
            return  False
    if log_type in COMPONENT:
        if not job_id or not role or not party_id or not component_name:
            return False
    return True


class LogCollector():
    def __init__(self, log_type, job_id, party_id="", role="", component_name="", **kwargs):
        self.log_type = log_type
        self.job_id = job_id
        self.party_id = str(party_id)
        self.role = role
        self.component_name = component_name

    def get_log_file_path(self):
        status = parameters_check(self.log_type, self.job_id, self.role, self.party_id, self.component_name)
        if not status:
            raise Exception(f"job type {self.log_type} Missing parameters")
        type_dict = {
            "jobSchedule": os.path.join(self.job_id, "fate_flow_schedule.log"),
            "jobScheduleError": os.path.join(self.job_id, "fate_flow_schedule_error.log"),
            "partyError": os.path.join(self.job_id, self.role, self.party_id, "ERROR.log"),
            "partyWarning": os.path.join(self.job_id, self.role, self.party_id, "WARNING.log"),
            "partyInfo": os.path.join(self.job_id,self.role, self.party_id, "INFO.log"),
            "partyDebug": os.path.join(self.job_id, self.role, self.party_id, "DEBUG.log"),
            "componentInfo": os.path.join(self.job_id, self.role, self.party_id, self.component_name, "INFO.log")
        }
        if self.log_type not in type_dict.keys():
            raise Exception(f"no found log  type {self.log_type}")
        return os.path.join(get_fate_flow_directory('logs'), type_dict[self.log_type])

    def cat_log(self, begin, end):
        line_list = []
        if begin and end:
            cmd = f"cat {self.get_log_file_path()} | tail -n +{begin}| head -n {end-begin+1}"
        else:
            cmd = f"cat {self.get_log_file_path()}"
        lines = self.execute(cmd)
        if lines:
            line_list = []
            line_num = begin if begin else 1
            for line in lines.strip().split("\n"):
                match_ip = re.findall('[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}', line)
                if match_ip:
                    for ip in match_ip:
                        line = re.sub(ip, "xxx.xxx.xxx.xxx", line)
                line_list.append({"line_num": line_num, "content": line})
                line_num += 1
        return line_list

    def get_size(self):
        try:
            return int(self.execute(f"cat {self.get_log_file_path()} |wc -l").strip())
        except:
            return 0

    @staticmethod
    def execute(cmd):
        res = os.popen(cmd)
        data = res.read()
        res.close()
        return data

