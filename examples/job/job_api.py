import requests
from ruamel import yaml

base = "http://127.0.0.1:9380/v2"


def submit_job():
    uri = "/job/submit"
    dag = yaml.safe_load(open("dag_conf.yaml", "r"))
    response = requests.post(base+uri,  json={"dag_schema": dag})
    print(response.text)


def query_job():
    uri = "/job/query"
    response = requests.post(base+uri,  json={"job_id": "202212121834588387430"})
    print(response.text)


def stop_job():
    uri = "/job/stop"
    response = requests.post(base+uri,  json={"job_id": "202212061236023583310"})
    print(response.text)


def query_task():
    uri = "/job/task/query"
    response = requests.post(base+uri,  json={"job_id": "202212121834588387430", "role": "guest", "party_id": "9999", "task_name": "reader_0"})
    print(response.text)

submit_job()



