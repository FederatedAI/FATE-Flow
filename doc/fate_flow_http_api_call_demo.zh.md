# REST API 调用

## 1. 说明
###  使用python请求fate flow 接口

## 2. 数据上传/下载

```python
import json
import os

import requests
from anaconda_project.internal.test.multipart import MultipartEncoder

base_url = "http://127.0.0.1:9380/v1"


def upload():
    uri = "/data/upload"
    file_name = "./data/breast_hetero_guest.csv"
    with open(file_name, 'rb') as fp:
        data = MultipartEncoder(
            fields={'file': (os.path.basename(file_name), fp, 'application/octet-stream')}
        )
        config_data = {
            "file": file_name,
            "id_delimiter": ",",
            "head": 1,
            "partition": 4,
            "namespace": "experiment",
            "table_name": "breast_hetero_guest"
        }

        response = requests.post(
            url=base_url + uri,
            data=data,
            params=json.dumps(config_data),
            headers={'Content-Type': data.content_type}
        )
        print(response.text)


def download():
    uri = "/data/download"
    config_data = {
        "output_path": "./download_breast_guest.csv",
        "namespace": "experiment",
        "table_name": "breast_hetero_guest"
    }
    response = requests.post(url=base_url + uri, json=config_data)
    print(response.text)


def upload_history():
    uri = "/data/upload/history"
    config_data = {
        "limit": 5
    }
    response = requests.post(url=base_url + uri, json=config_data)
    print(response.text)


```
## 3. 数据表操作
```python
import requests

base_url = "http://127.0.0.1:9380/v1"


def table_bind():
    uri = "/table/bind"
    data = {
        "head": 1,
        "partition": 8,
        "address": {"user": "fate", "passwd": "fate", "host": "127.0.0.1", "port": 3306, "db": "xxx", "name": "xxx"},
        "id_name": "id",
        "feature_column": "y,x0,x1,x2,x3,x4,x5,x6,x7,x8,x9,x10,x11,x12",
        "engine": "MYSQL",
        "id_delimiter": ",",
        "namespace": "wzh",
        "name": "wzh",
    }
    res = requests.post(base_url + uri, json=data)
    print(res.text)


def table_delete():
    uri = "/table/delete"
    data = {
        "table_name": "breast_hetero_guest",
        "namespace": "experiment"
    }
    res = requests.post(base_url + uri, json=data)
    print(res.text)


def table_info():
    uri = "/table/table_info"
    data = {
        "table_name": "xxx",
        "namespace": "xxx"
    }
    res = requests.post(base_url + uri, json=data)
    print(res.text)


def table_list():
    uri = "/table/list"
    data = {"job_id": "202204221515021092240", "role": "guest", "party_id": "20001"}
    res = requests.post(base_url + uri, json=data)
    print(res.text)


def tracking_source():
    uri = "/table/tracking/source"
    data = {"table_name": "xxx", "namespace": "xxx"}
    res = requests.post(base_url + uri, json=data)
    print(res.text)


def tracking_job():
    uri = "/table/tracking/job"
    data = {"table_name": "xxx", "namespace": "xxx"}
    res = requests.post(base_url + uri, json=data)
    print(res.text)

```

## 4. 任务

```python

import tarfile

import requests

base_url = "http:/127.0.0.1:9380/v1"


def submit():
    uri = "/job/submit"
    data = {
        "dsl": {
            "components": {
                "reader_0": {
                    "module": "Reader",
                    "output": {
                        "data": [
                            "table"
                        ]
                    }
                },
                "dataio_0": {
                    "module": "DataIO",
                    "input": {
                        "data": {
                            "data": [
                                "reader_0.table"
                            ]
                        }
                    },
                    "output": {
                        "data": [
                            "train"
                        ],
                        "model": [
                            "dataio"
                        ]
                    },
                    "need_deploy": True
                },
                "intersection_0": {
                    "module": "Intersection",
                    "input": {
                        "data": {
                            "data": [
                                "dataio_0.train"
                            ]
                        }
                    },
                    "output": {
                        "data": [
                            "train"
                        ]
                    }
                },
                "hetero_feature_binning_0": {
                    "module": "HeteroFeatureBinning",
                    "input": {
                        "data": {
                            "data": [
                                "intersection_0.train"
                            ]
                        }
                    },
                    "output": {
                        "data": [
                            "train"
                        ],
                        "model": [
                            "hetero_feature_binning"
                        ]
                    }
                },
                "hetero_feature_selection_0": {
                    "module": "HeteroFeatureSelection",
                    "input": {
                        "data": {
                            "data": [
                                "hetero_feature_binning_0.train"
                            ]
                        },
                        "isometric_model": [
                            "hetero_feature_binning_0.hetero_feature_binning"
                        ]
                    },
                    "output": {
                        "data": [
                            "train"
                        ],
                        "model": [
                            "selected"
                        ]
                    }
                },
                "hetero_lr_0": {
                    "module": "HeteroLR",
                    "input": {
                        "data": {
                            "train_data": [
                                "hetero_feature_selection_0.train"
                            ]
                        }
                    },
                    "output": {
                        "data": [
                            "train"
                        ],
                        "model": [
                            "hetero_lr"
                        ]
                    }
                },
                "evaluation_0": {
                    "module": "Evaluation",
                    "input": {
                        "data": {
                            "data": [
                                "hetero_lr_0.train"
                            ]
                        }
                    },
                    "output": {
                        "data": [
                            "evaluate"
                        ]
                    }
                }
            }
        },
        "runtime_conf": {
            "dsl_version": "2",
            "initiator": {
                "role": "guest",
                "party_id": 20001
            },
            "role": {
                "guest": [
                    20001
                ],
                "host": [
                    10001
                ],
                "arbiter": [
                    10001
                ]
            },
            "job_parameters": {
                "common": {
                    "task_parallelism": 2,
                    "computing_partitions": 8,
                    "task_cores": 4,
                    "auto_retries": 1
                }
            },
            "component_parameters": {
                "common": {
                    "intersection_0": {
                        "intersect_method": "raw",
                        "sync_intersect_ids": True,
                        "only_output_key": False
                    },
                    "hetero_lr_0": {
                        "penalty": "L2",
                        "optimizer": "rmsprop",
                        "alpha": 0.01,
                        "max_iter": 3,
                        "batch_size": 320,
                        "learning_rate": 0.15,
                        "init_param": {
                            "init_method": "random_uniform"
                        }
                    }
                },
                "role": {
                    "guest": {
                        "0": {
                            "reader_0": {
                                "table": {
                                    "name": "breast_hetero_guest",
                                    "namespace": "experiment"
                                }
                            },
                            "dataio_0": {
                                "with_label": True,
                                "label_name": "y",
                                "label_type": "int",
                                "output_format": "dense"
                            }
                        }
                    },
                    "host": {
                        "0": {
                            "reader_0": {
                                "table": {
                                    "name": "breast_hetero_host",
                                    "namespace": "experiment"
                                }
                            },
                            "dataio_0": {
                                "with_label": False,
                                "output_format": "dense"
                            },
                            "evaluation_0": {
                                "need_run": False
                            }
                        }
                    }
                }
            }
        }
    }
    res = requests.post(base_url + uri, json=data)
    print(res.text)


def stop():
    uri = "/job/stop"
    data = {"job_id": "202204251958539401540"}
    res = requests.post(base_url + uri, json=data)
    print(res.text)


def rerun():
    uri = "/job/rerun"
    data = {"job_id": "202204251958539401540"}
    res = requests.post(base_url + uri, json=data)
    print(res.text)


def query():
    uri = "/job/query"
    data = {"job_id": "202204251958539401540"}
    res = requests.post(base_url + uri, json=data)
    print(res.text)


def list_job():
    uri = "/job/list/job"
    data = {"limit": 1}
    res = requests.post(base_url + uri, json=data)
    print(res.text)


def update():
    uri = "/job/update"
    data = {"job_id": "202204251958539401540", "role": "guest", "party_id": 20001, "notes": "this is a test"}
    res = requests.post(base_url + uri, json=data)
    print(res.text)


def parameter_update():
    uri = "/job/parameter/update"
    data = {"component_parameters": {"common": {"hetero_lr_0": {"max_iter": 10}}},
            "job_parameters": {"common": {"auto_retries": 2}}, "job_id": "202204251958539401540"}
    res = requests.post(base_url + uri, json=data)
    print(res.text)


def config():
    uri = "/job/config"
    data = {"job_id": "202204251958539401540"}
    res = requests.post(base_url + uri, json=data)
    print(res.text)


def log_download():
    uri = "/job/log/download"
    data = {"job_id": "202204251958539401540a"}
    download_tar_file_name = "./test.tar.gz"
    res = requests.post(base_url + uri, json=data)
    with open(download_tar_file_name, "wb") as fw:
        for chunk in res.iter_content(1024):
            if chunk:
                fw.write(chunk)
    tar = tarfile.open(download_tar_file_name, "r:gz")
    file_names = tar.getnames()
    for file_name in file_names:
        tar.extract(file_name)
    tar.close()


def log_path():
    uri = "/job/log/path"
    data = {"job_id": "202204251958539401540"}
    res = requests.post(base_url + uri, json=data)
    print(res.text)


def task_query():
    uri = "/job/task/query"
    data = {"job_id": "202204251958539401540", "role": "guest", "party_id": 20001}
    res = requests.post(base_url + uri, json=data)
    print(res.text)


def list_task():
    uri = "/job/list/task"
    data = {"job_id": "202204251958539401540", "role": "guest", "party_id": 20001}
    res = requests.post(base_url + uri, json=data)
    print(res.text)

def job_clean():
    uri = "/job/clean"
    data = {"job_id": "202204251958539401540", "role": "guest", "party_id": 20001}
    res = requests.post(base_url + uri, json=data)
    print(res.text)

def clean_queue():
    uri = "/job/clean/queue"
    res = requests.post(base_url + uri)
    print(res.text)


```

## 5. 指标
```python
import tarfile

import requests

base_url = "http://127.0.0.1:9380/v1"


def job_data_view():
    uri = "/tracking/job/data_view"
    data = {"job_id": "202203311009181495690", "role": "guest", "party_id": 20001}
    res = requests.post(base_url + uri, json=data)
    print(res.text)


def component_metric_all():
    uri = "/tracking/component/metric/all"
    data = {"job_id": "202203311009181495690", "role": "guest", "party_id": 20001, "component_name": "HeteroSecureBoost_0"}
    res = requests.post(base_url + uri, json=data)
    print(res.text)
# {"data":{"train":{"loss":{"data":[[0,0.6076415445876732],[1,0.5374539452565573],[2,0.4778598986135903],[3,0.42733599866560723],[4,0.38433409799127843]],"meta":{"Best":0.38433409799127843,"curve_name":"loss","metric_type":"LOSS","name":"train","unit_name":"iters"}}}},"retcode":0,"retmsg":"success"}


def component_metric():
    uri = "/tracking/component/metrics"
    data = {"job_id": "202203311009181495690", "role": "guest", "party_id": 20001, "component_name": "Intersection_0"}
    res = requests.post(base_url + uri, json=data)
    print(res.text)

def component_metric_data():
    uri = "/tracking/component/metric_data"
    data = {"job_id": "202203311009181495690",
            "role": "guest",
            "party_id": 20001,
            "component_name": "Intersection_0",
            "metric_name": "intersection",
            "metric_namespace": "train"}
    res = requests.post(base_url + uri, json=data)
    print(res.text)


def component_parameters():
    uri = "/tracking/component/parameters"
    data = {"job_id": "202203311009181495690",
            "role": "guest",
            "party_id": 20001,
            "component_name": "Intersection_0"}
    res = requests.post(base_url + uri, json=data)
    print(res.text)


def component_output_model():
    uri = "/tracking/component/output/model"
    data = {"job_id": "202203311009181495690",
            "role": "guest",
            "party_id": 20001,
            "component_name": "Intersection_0"}
    res = requests.post(base_url + uri, json=data)
    print(res.text)


def component_output_data():
    uri = "/tracking/component/output/data"
    data = {"job_id": "202203311009181495690",
            "role": "guest",
            "party_id": 20001,
            "component_name": "Intersection_0"}
    res = requests.post(base_url + uri, json=data)
    print(res.text)


def component_output_data_download():
    uri = "/tracking/component/output/data/download"
    download_tar_file_name = "data.tar.gz"
    data = {"job_id": "202203311009181495690",
            "role": "guest",
            "party_id": 20001,
            "component_name": "Intersection_0"}
    res = requests.get(base_url + uri, json=data)
    print(res.text)
    with open(download_tar_file_name, "wb") as fw:
        for chunk in res.iter_content(1024):
            if chunk:
                fw.write(chunk)
    tar = tarfile.open(download_tar_file_name, "r:gz")
    file_names = tar.getnames()
    for file_name in file_names:
        tar.extract(file_name)
    tar.close()


def component_output_data_table():
    uri = "/tracking/component/output/data/table"
    data = {"job_id": "202203311009181495690",
            "role": "guest",
            "party_id": 20001,
            "component_name": "Intersection_0a"}
    res = requests.post(base_url + uri, json=data)
    print(res.text)


def component_component_summary_download():
    uri = "/tracking/component/summary/download"
    data = {"job_id": "202203311009181495690",
            "role": "guest",
            "party_id": 20001,
            "component_name": "Intersection_0"}
    res = requests.post(base_url + uri, json=data)
    print(res.text)


def component_list():
    uri = "/tracking/component/list"
    data = {"job_id": "202203311009181495690"}
    res = requests.post(base_url + uri, json=data)
    print(res.text)
component_list()
```

## 6. 资源
```python
import requests

base_url = "http://127.0.0.1:9380/v1"


def resource_query():
    uri = "/resource/query"
    data = {"engine_name": "EGGROLL"}
    res = requests.post(base_url + uri, json=data)
    print(res.text)



def resource_return():
    uri = "/resource/return"
    data = {"job_id": "202204261616175720130"}
    res = requests.post(base_url + uri, json=data)
    print(res.text)
resource_return()
```

## 7. 权限
```python
import requests

base_url = "http://127.0.0.1:9380/v1"


def grant_privilege():
    uri = "/permission/grant/privilege"
    data = {
        "src_role": "guest",
        "src_party_id": "9999",
        "privilege_role": "all",
        "privilege_component": "all",
        "privilege_command": "all"
    }
    res = requests.post(base_url + uri, json=data)
    print(res.text)

# grant_privilege()

def delete_privilege():
    uri = "/permission/delete/privilege"
    data = {
        "src_role": "guest",
        "src_party_id": "9999",
        "privilege_role": "guest",
        "privilege_component": "dataio",
        "privilege_command": "create"
    }
    res = requests.post(base_url + uri, json=data)
    print(res.text)

# delete_privilege()


def query_privilege():
    uri = "/permission/query/privilege"
    data = {
        "src_role": "guest",
        "src_party_id": "9999"
    }
    res = requests.post(base_url + uri, json=data)
    print(res.text)

query_privilege()

```


