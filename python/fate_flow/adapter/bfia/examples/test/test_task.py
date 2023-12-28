import json

import requests

base_url = "http://127.0.0.1:9380"


def start_task(job_id, task_id, task_name):
    uri = "/v1/interconn/schedule/task/start"
    resp = requests.post(base_url+uri, json={"job_id": job_id, "task_id": task_id, "task_name": task_name})
    print(resp.text)


def stop_job(job_id):
    uri = "/v1/platform/schedule/job/stop_all"
    resp = requests.post(base_url+uri, json={"job_id": job_id})
    print(resp.text)


# submit_job()
# start_task("202310161542273925260", "202310161422165657200_wzh3", "intersect_rsa_1")
# stop_job("202310161542273925260")
