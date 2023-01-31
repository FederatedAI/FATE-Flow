import requests

base = "http://127.0.0.1:9380/v2"


def metric_key_query(job_id, role, party_id, task_name):
    uri = "/output/metric/key/query"
    data = {
        "job_id": job_id,
        "role": role,
        "party_id": party_id,
        "task_name": task_name
    }
    response = requests.get(base+uri,  params=data)
    print(response.text)


def metric_query(job_id, role, party_id, task_name):
    uri = "/output/metric/query"
    data = {
        "job_id": job_id,
        "role": role,
        "party_id": party_id,
        "task_name": task_name
    }
    response = requests.get(base+uri,  params=data)
    print(response.text)


def model_query(job_id, role, party_id, task_name):
    uri = "/output/model/query"
    data = {
        "job_id": job_id,
        "role": role,
        "party_id": party_id,
        "task_name": task_name
    }
    response = requests.get(base+uri,  params=data)
    print(response.text)
