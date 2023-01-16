import requests
from ruamel import yaml

base = "http://127.0.0.1:9380/v2"


def submit_job():
    uri = "/job/submit"
    dag = yaml.safe_load(open("./../lr/standalone/lr_train_dag.yaml", "r"))
    response = requests.post(base+uri,  json={"dag_schema": dag})
    print(response.text)


def query_job(job_id):
    uri = "/job/query"
    response = requests.post(base+uri,  json={"job_id": job_id})
    print(response.text)


def stop_job(job_id):
    uri = "/job/stop"
    response = requests.post(base+uri,  json={"job_id": job_id})
    print(response.text)


def query_task(job_id, role, party_id, task_name):
    uri = "/job/task/query"
    response = requests.post(base+uri,  json={"job_id": job_id, "role": role, "party_id": party_id, "task_name": task_name})
    print(response.text)
