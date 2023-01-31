import json

import requests

base = "http://127.0.0.1:9380/v2"


def upload_data():
    uri = "/data/upload"
    conf = json.load(open("../upload/upload_guest.json", "r"))
    response = requests.post(base+uri,  json=conf)
    print(response.text)
