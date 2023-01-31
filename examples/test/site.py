import requests

base = "http://127.0.0.1:9380/v2"


def site_info_query():
    uri = "/site/info/query"
    response = requests.get(base+uri)
    print(response.text)
