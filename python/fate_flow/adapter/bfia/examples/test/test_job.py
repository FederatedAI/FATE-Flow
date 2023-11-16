import json

import requests

base_url = "http://127.0.0.1:9380"


def register_components():
    uri = "/v2/provider/register"
    config_path = "../job/fate/fate_components.json"
    body = json.load(open(config_path, "r"))
    resp = requests.post(base_url+uri, json=body)
    print(resp.text)


register_components()


def submit_job():
    uri = "/v1/platform/schedule/job/create_all"
    config_path = "../job/fate/fate_psi_lr.json"
    body = json.load(open(config_path, "r"))
    resp = requests.post(base_url+uri, json=body)
    print(resp.text)


def start_job(job_id):
    uri = "/v1/interconn/schedule/job/start"
    resp = requests.post(base_url+uri, json={"job_id": job_id})
    print(resp.text)


def stop_job(job_id):
    uri = "/v1/interconn/schedule/job/stop_all"
    resp = requests.post(base_url+uri, json={"job_id": job_id})
    print(resp.text)


submit_job()
