---

name: Bug Report
about: Use this template for reporting a bug
labels: 'type:bug'

---

**System information**

- Have I written custom code (yes/no):
- OS Platform and Distribution (e.g., Linux Ubuntu 16.04):
- FATE Flow version (use command: python fate_flow_server.py --version):
- Python version (use command: python --version):

**Describe the current behavior**

**Describe the expected behavior**

**Other info / logs** Include any logs or source code that would be helpful to
diagnose the problem. If including tracebacks, please include the full
traceback. Large logs and files should be attached.

- fateflow/logs/$job_id/fate_flow_schedule.log: scheduling log for a job
- fateflow/logs/$job_id/* : all logs for a job
- fateflow/logs/fate_flow/fate_flow_stat.log: a log of server stat
- fateflow/logs/fate_flow/fate_flow_schedule.log: the starting scheduling log for all jobs
- fateflow/logs/fate_flow/fate_flow_detect.log: the starting detecting log for all jobs

**Contributing**

- Do you want to contribute a PR? (yes/no):
- Briefly describe your candidate solution(if contributing):
