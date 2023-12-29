# Quick Start

## 1. Environment Setup
You can choose from the following three deployment modes based on your requirements:

### 1.1 Pypi Package Installation
Explanation: This mode operates in a single-machine environment.

#### 1.1.1 Installation
- Prepare and install [conda](https://docs.conda.io/projects/miniconda/en/latest/) environment.
- Create a virtual environment:
```shell
# FATE requires python>=3.8
conda create -n fate_env python=3.8
conda activate fate_env
```
- Install FATE Flow and related dependencies:
```shell
pip install fate_client[fate,fate_flow]==2.0.0
```

#### 1.1.2 Service Initialization
```shell
fate_flow init --ip 127.0.0.1 --port 9380 --home $HOME_DIR
```
- ip: Service running IP
- port: HTTP port for the service
- home: Data storage directory, including data/models/logs/job configurations/sqlite.db, etc.

#### 1.1.3 Service Start/Stop
```shell
fate_flow status/start/stop/restart
```

### 1.2 Standalone Deployment
Refer to [Standalone Deployment](https://github.com/FederatedAI/FATE/tree/v2.0.0/deploy/standalone-deploy/README.zh.md)

### 1.3 Cluster Deployment
Refer to [Allinone Deployment](https://github.com/FederatedAI/FATE/tree/v2.0.0/deploy/cluster-deploy/allinone/fate-allinone_deployment_guide.zh.md)

## 2. User Guide
FATE provides a client package including SDK, CLI, and Pipeline. If FATE Client isn't deployed in your environment, you can download it using `pip install fate_client`. The following operations are CLI-based.

### 2.1 Data Upload
For detailed data operation guides, refer to [Data Access Guide](data_access.zh.md)
### 2.1.1 Configuration and Data
 - Upload Configuration: [examples-upload](https://github.com/FederatedAI/FATE-Flow/tree/v2.0.0/examples/upload)
 - Upload Data: [upload-data](https://github.com/FederatedAI/FATE-Flow/tree/v2.0.0/examples/data)
### 2.1.2 Upload Guest Data
```shell
flow data upload -c examples/upload/upload_guest.json
```
### 2.1.3 Upload Host Data
```shell
flow data upload -c examples/upload/upload_host.json
```

### 2.2 Starting a FATE Job
#### 2.2.1 Submitting a Job
Once your data is prepared, you can submit a job to FATE Flow:
- Job configuration examples are in [lr-train](https://github.com/FederatedAI/FATE-Flow/tree/v2.0.0/examples/lr/train_lr.yaml).
- Site IDs in the job configuration are "9998" and "9999". Replace them with real site IDs for cluster deployments; default configuration can be used for standalone deployments.
- If you want to use your data, modify the parameters in the reader within the configuration.
- Command to submit a job:
```shell
flow job submit -c examples/lr/train_lr.yaml 
```
- Successful submission returns:
```json
{
    "code": 0,
    "data": {
        "model_id": "202308211911505128750",
        "model_version": "0"
    },
    "job_id": "202308211911505128750",
    "message": "success"
}

```
The "data" here contains the output of the job, i.e., the model.

#### 2.2.2 Querying a Job
During job execution, you can query the job status using the query command:
```shell
flow job query -j $job_id
```

#### 2.2.3 Stopping a Job
While the job is running, you can stop it using the stop job command:
```shell
flow job stop -j $job_id
```

#### 2.2.4 Rerunning a Job
If a job fails during execution, you can rerun it using the rerun command:
```shell
flow job rerun -j $job_id
```

### 2.3 Fetching Job Output
Job output includes data, models, and metrics.
#### 2.3.1 Output Metrics
Querying output metrics command:
```shell
flow output query-metric -j $job_id -r $role -p $party_id -tn $task_name
```
For example, with the previously submitted training DAG task, you can use `flow output query-metric -j 202308211911505128750 -r arbiter -p 9998 -tn lr_0` to query. The result looks like this:
```json
{
    "code": 0,
    "data": [
        {
            "data": [
                {
                    "metric": [
                        0.0
                    ],
                    "step": 0,
                    "timestamp": 1692616428.253495
                }
            ],
            "groups": [
                {
                    "index": null,
                    "name": "default"
                },
                {
                    "index": null,
                    "name": "train"
                }
            ],
            "name": "lr_loss",
            "step_axis": "iterations",
            "type": "loss"
        },
        {
            "data": [
                {
                    "metric": [
                        -0.07785049080848694
                    ],
                    "step": 1,
                    "timestamp": 1692616432.9727712
                }
            ],
            "groups": [
                {
                    "index": null,
                    "name": "default"
                },
                {
                    "index": null,
                    "name": "train"
                }
            ],
            "name": "lr_loss",
            "step_axis": "iterations",
            "type": "loss"
        }
    ],
    "message": "success"
}

```


#### 2.3.2 Output Models
##### 2.3.2.1 Querying Models
```shell
flow output query-model -j $job_id -r $role -p $party_id -tn $task_name
```
For instance, with the previously submitted training DAG task, you can use `flow output query-model -j 202308211911505128750 -r host -p 9998 -tn lr_0` to query.
The query result looks like this:
```json
{
    "code": 0,
    "data": {
        "output_model": {
            "data": {
                "estimator": {
                    "end_epoch": 10,
                    "is_converged": false,
                    "lr_scheduler": {
                        "lr_params": {
                            "start_factor": 0.7,
                            "total_iters": 100
                        },
                        "lr_scheduler": {
                            "_get_lr_called_within_step": false,
                            "_last_lr": [
                                0.07269999999999996
                            ],
                            "_step_count": 10,
                            "base_lrs": [
                                0.1
                            ],
                            "end_factor": 1.0,
                            "last_epoch": 9,
                            "start_factor": 0.7,
                            "total_iters": 100,
                            "verbose": false
                        },
                        "method": "linear"
                    },
                    "optimizer": {
                        "alpha": 0.001,
                        "l1_penalty": false,
                        "l2_penalty": true,
                        "method": "sgd",
                        "model_parameter": [
                            [
                                0.0
                            ],
                            [
                                0.0
                            ],
                            [
                                0.0
                            ],
                            [
                                0.0
                            ],
                            [
                                0.0
                            ],
                            [
                                0.0
                            ],
                            [
                                0.0
                            ],
                            [
                                0.0
                            ],
                            [
                                0.0
                            ],
                            [
                                0.0
                            ],
                            [
                                0.0
                            ],
                            [
                                0.0
                            ],
                            [
                                0.0
                            ],
                            [
                                0.0
                            ],
                            [
                                0.0
                            ],
                            [
                                0.0
                            ],
                            [
                                0.0
                            ],
                            [
                                0.0
                            ],
                            [
                                0.0
                            ],
                            [
                                0.0
                            ]
                        ],
                        "model_parameter_dtype": "float32",
                        "optim_param": {
                            "lr": 0.1
                        },
                        "optimizer": {
                            "param_groups": [
                                {
                                    "dampening": 0,
                                    "differentiable": false,
                                    "foreach": null,
                                    "initial_lr": 0.1,
                                    "lr": 0.07269999999999996,
                                    "maximize": false,
                                    "momentum": 0,
                                    "nesterov": false,
                                    "params": [
                                        0
                                    ],
                                    "weight_decay": 0
                                }
                            ],
                            "state": {}
                        }
                    },
                    "param": {
                        "coef_": [
                            [
                                -0.10828543454408646
                            ],
                            [
                                -0.07341302931308746
                            ],
                            [
                                -0.10850320011377335
                            ],
                            [
                                -0.10066638141870499
                            ],
                            [
                                -0.04595951363444328
                            ],
                            [
                                -0.07001449167728424
                            ],
                            [
                                -0.08949052542448044
                            ],
                            [
                                -0.10958756506443024
                            ],
                            [
                                -0.04012322425842285
                            ],
                            [
                                0.02270071767270565
                            ],
                            [
                                -0.07198350876569748
                            ],
                            [
                                0.00548586156219244
                            ],
                            [
                                -0.06599288433790207
                            ],
                            [
                                -0.06410090625286102
                            ],
                            [
                                0.016374297440052032
                            ],
                            [
                                -0.01607361063361168
                            ],
                            [
                                -0.011447405442595482
                            ],
                            [
                                -0.04352564364671707
                            ],
                            [
                                0.013161249458789825
                            ],
                            [
                                0.013506329618394375
                            ]
                        ],
                        "dtype": "float32",
                        "intercept_": null
                    }
                }
            },
            "meta": {
                "batch_size": null,
                "epochs": 10,
                "init_param": {
                    "fill_val": 0.0,
                    "fit_intercept": false,
                    "method": "zeros",
                    "random_state": null
                },
                "label_count": false,
                "learning_rate_param": {
                    "method": "linear",
                    "scheduler_params": {
                        "start_factor": 0.7,
                        "total_iters": 100
                    }
                },
                "optimizer_param": {
                    "alpha": 0.001,
                    "method": "sgd",
                    "optimizer_params": {
                        "lr": 0.1
                    },
                    "penalty": "l2"
                },
                "ovr": false
            }
        }
    },
    "message": "success"
}

```

##### 2.3.2.2 Downloading Models
```shell 
flow output download-model -j $job_id -r $role -p $party_id -tn $task_name -o $download_dir
```
For example, with the previously submitted training DAG task, you can use `flow output download-model -j 202308211911505128750 -r host -p 9998 -tn lr_0 -o ./` to download.
The download result is shown below:
```json
{
    "code": 0,
    "directory": "./output_model_202308211911505128750_host_9998_lr_0",
    "message": "download success, please check the path: ./output_model_202308211911505128750_host_9998_lr_0"
}


```

### 2.3.3 Output Data
#### 2.3.3.1 Query Data Table
```shell
flow output query-data-table -j $job_id -r $role -p $party_id -tn $task_name
```
For instance, with the previously submitted training DAG task, you can use `flow output query-data-table -j 202308211911505128750 -r host -p 9998 -tn binning_0` to query. The result looks like this:
```json
{
    "train_output_data": [
        {
            "name": "9e28049c401311ee85c716b977118319",
            "namespace": "202308211911505128750_binning_0"
        }
    ]
}
```

#### 2.3.3.2 Preview Data
```shell
flow output display-data -j $job_id -r $role -p $party_id -tn $task_name
```
For example, with the previously submitted training DAG task, you can use `flow output display-data -j 202308211911505128750 -r host -p 9998 -tn binning_0` to preview output data.

#### 2.3.3.3 Download Data
```shell
flow output download-data -j $job_id -r $role -p $party_id -tn $task_name -o $download_dir
```
For example, with the previously submitted training DAG task, you can use `flow output download-data -j 202308211911505128750 -r guest -p 9999 -tn lr_0 -o ./` to download output data. The download result is as follows:
```json
{
    "code": 0,
    "directory": "./output_data_202308211911505128750_guest_9999_lr_0",
    "message": "download success, please check the path: ./output_data_202308211911505128750_guest_9999_lr_0"
}
```

## 3. More Documentation
- [Restful-api](https://github.com/FederatedAI/FATE-Flow/tree/v2.0.0/doc/swagger/swagger.yaml)
- [CLI](https://github.com/FederatedAI/FATE-Client/tree/v2.0.0/python/fate_client/flow_cli/build/doc)
- [Pipeline](https://github.com/FederatedAI/FATE/tree/v2.0.0/doc/tutorial)
- [FATE Quick Start](https://github.com/FederatedAI/FATE/tree/v2.0.0/doc/2.0/fate/quick_start.md)
- [FATE Algorithms](https://github.com/FederatedAI/FATE/tree/v2.0.0/doc/2.0/fate)