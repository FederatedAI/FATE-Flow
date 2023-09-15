# Quick Start

## 1. Environment Setup
You can choose one of the following three deployment modes based on your requirements:

### 1.1 Pypi Package Installation
Note: This mode operates in a single-machine mode.

#### 1.1.1 Installation
- Prepare and install [conda](https://docs.conda.io/projects/miniconda/en/latest/) environment.
- Create a virtual environment:
```shell
# FATE requires Python >= 3.8
conda create -n fate_env python=3.8
conda activate fate_env
```
- Install FATE Flow and related dependencies:
```shell
pip install fate_client[fate,fate_flow]==2.0.0.b0
```

#### 1.1.2 Service Initialization
```shell
fate_flow init --ip 127.0.0.1 --port 9380 --home $HOME_DIR
```
- `ip`: The IP address where the service runs.
- `port`: The HTTP port the service runs on.
- `home`: The data storage directory, including data, models, logs, job configurations, and SQLite databases.

#### 1.1.3 Service Start/Stop
```shell
fate_flow status/start/stop/restart
```

### 1.2 Standalone Deployment
Refer to [Standalone Deployment](https://github.com/FederatedAI/FATE/tree/v2.0.0-beta/deploy/standalone-deploy/README.zh.md).

### 1.3 Cluster Deployment
Refer to [Allinone Deployment](https://github.com/FederatedAI/FATE/tree/v2.0.0-beta/deploy/cluster-deploy/allinone/fate-allinone_deployment_guide.zh.md).

## 2. User Guide
FATE provides client tools including SDK, CLI, and Pipeline. If you don't have FATE Client deployed in your environment, you can download it using `pip install fate_client`. The following operations are based on CLI.

### 2.1 Data Upload
In version 2.0-beta, data uploading is a two-step process:

- **upload**: Uploads data to FATE-supported storage services.
- **transformer**: Transforms data into a DataFrame.

#### 2.1.1 upload
##### 2.1.1.1 Configuration and Data
- Upload configuration can be found at [examples-upload](https://github.com/FederatedAI/FATE-Flow/tree/v2.0.0-beta/examples/upload), and the data is located at [upload-data](https://github.com/FederatedAI/FATE-Flow/tree/v2.0.0-beta/examples/data).
- You can also use your own data and modify the "meta" information in the upload configuration.

##### 2.1.1.2 Upload Guest Data
```shell
flow data upload -c examples/upload/upload_guest.json
```
- Record the returned "name" and "namespace" for use in the transformer phase.

##### 2.1.1.3 Upload Host Data
```shell
flow data upload -c examples/upload/upload_host.json
```
- Record the returned "name" and "namespace" for use in the transformer phase.

##### 2.1.1.4 Upload Result
```json
{
    "code": 0,
    "data": {
        "name": "36491bc8-3fef-11ee-be05-16b977118319",
        "namespace": "upload"
    },
    "job_id": "202308211451535620150",
    "message": "success"
}
```
Where "namespace" and "name" identify the data in FATE for future reference in the transformer phase.

##### 2.1.1.5 Data Query
Since upload is an asynchronous operation, you need to confirm if it was successful before proceeding to the next step.
```shell
flow table query --namespace upload --name 36491bc8-3fef-11ee-be05-16b977118319
```
If the returned code is 0, the upload was successful.

#### 2.1.2 Transformer
##### 2.1.2.1 Configuration
- Transformer configuration can be found at [examples-transformer](https://github.com/FederatedAI/FATE-Flow/tree/v2.0.0-beta/examples/transformer).

##### 2.1.2.2 Transform Guest Data
- Configuration path: examples/transformer/transformer_guest.json
- Modify the "namespace" and "name" in the "data_warehouse" section to match the output from the guest data upload.
```shell
flow data transformer -c examples/transformer/transformer_guest.json
```

##### 2.1.2.3 Transform Host Data
- Configuration path: examples/transformer/transformer_host.json
- Modify the "namespace" and "name" in the "data_warehouse" section to match the output from the host data upload.
```shell
flow data transformer -c examples/transformer/transformer_host.json
```

##### 2.1.2.4 Transformer Result
```json
{
    "code": 0,
    "data": {
        "name": "breast_hetero_guest",
        "namespace": "experiment"
    },
    "job_id": "202308211557455662860",
    "message": "success"
}
```
Where "namespace" and "name" identify the data in FATE for future modeling jobs.

##### 2.1.2.5 Check if Data Upload Was Successful
Since the transformer is also an asynchronous operation, you need to confirm if it was successful before proceeding.
```shell
flow table query --namespace experiment --name breast_hetero_guest
```
```shell
flow table query --namespace experiment --name breast_hetero_host
```
If the returned code is 0, the upload was successful.

### 2.2 Starting FATE Jobs
#### 2.2.1 Submitting a Job
Once your data is prepared, you can start submitting jobs to FATE Flow:

- The configuration for training jobs can be found in [lr-train](https://github.com/FederatedAI/FATE-Flow/tree/v2.0.0-beta/examples/lr/train_lr.yaml).
- The configuration for prediction jobs can be found in [lr-predict](https://github.com/FederatedAI/FATE-Flow/tree/v2.0.0-beta/examples/lr/predict_lr.yaml). To use it, modify the "dag.conf.model_warehouse" to point to the output model of your training job.
- In the training and prediction job configurations, the site IDs are set to "9998" and "9999." If your deployment environment is the cluster version, you need to replace them with the actual site IDs. For the standalone version, you can use the default configuration.
- If you want to use your own data, you can change the "namespace" and "name" of "data_warehouse" for both the guest and host in the configuration.
- To submit a job, use the following command:
```shell
flow job submit -c examples/lr/train_lr.yaml 
```
- A successful submission will return the following result:
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
The "data" section here contains the output model of the job.

#### 2.2.2 Querying a Job
While a job is running, you can check its status using the query command:
```shell
flow job query -j $job_id
```

#### 2.2.3 Stopping a Job
During job execution, you can stop the current job using the stop command:
```shell
flow job stop -j $job_id
```

#### 2.2.4 Rerunning a Job
If a job fails during execution, you can rerun it using the rerun command:
```shell
flow job rerun -j $job_id
```

### 2.3 Obtaining Job Outputs
Job outputs include data, models, and metrics.

#### 2.3.1 Output Metrics
To query output metrics, use the following command:
```shell
flow output query-metric -j $job_id -r $role -p $party_id -tn $task_name
```
For example, if you used the training DAG from above, you can use `flow output query-metric -j 202308211911505128750 -r arbiter -p 9998 -tn lr_0` to query metrics.
The query result will look like this:
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
To query output models, use the following command:
```shell
flow output query-model -j $job_id -r $role -p $party_id -tn $task_name
```
For example, if you used the training DAG from above, you can use `flow output query-model -j 202308211911505128750 -r host -p 9998 -tn lr_0` to query models.
The query result will be similar to this:

```json
{
    "code": 0,
    "data": [
        {
            "model": {
                "file": "202308211911505128750_host_9998_lr_0",
                "namespace": "202308211911505128750_host_9998_lr_0"
            },
            "name": "HeteroLRHost_9998_0",
            "namespace": "202308211911505128750_host_9998_lr_0",
            "role": "host",
            "party_id": "9998",
            "work_mode": 1
        }
    ],
    "message": "success"
}
```

##### 2.3.2.2 Downloading Models
To download models, use the following command:
```shell 
flow output download-model -j $job_id -r $role -p $party_id -tn $task_name -o $download_dir
```
For example, if you used the training DAG from above, you can use `flow output download-model -j 202308211911505128750 -r host -p 9998 -tn lr_0 -o ./` to download the model.
The download result will be similar to this:

```json
{
    "code": 0,
    "directory": "./output_model_202308211911505128750_host_9998_lr_0",
    "message": "download success, please check the path: ./output_model_202308211911505128750_host_9998_lr_0"
}
```

#### 2.3.3 Output Data
##### 2.3.3.1 Querying Data Tables
To query output data tables, use the following command:
```shell
flow output query-data-table -j $job_id -r $role -p $party_id -tn $task_name
```
For example, if you used the training DAG from above, you can use `flow output query-data-table -j 202308211911505128750 -r host -p 9998 -tn binning_0` to query data tables.
The query result will be similar to this:

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

##### 2.3.3.2 Preview Data
```shell
flow output display-data -j $job_id -r $role -p $party_id -tn $task_name
```
To preview output data using the above training DAG submission, you can use the following command: `flow output display-data -j 202308211911505128750 -r host -p 9998 -tn binning_0`.

##### 2.3.3.3 Download Data
```shell
flow output download-data -j $job_id -r $role -p $party_id -tn $task_name -o $download_dir
```
To download output data using the above training DAG submission, you can use the following command: `flow output download-data -j 202308211911505128750 -r guest -p 9999 -tn lr_0 -o ./`.

The download result will be as follows:
```json
{
    "code": 0,
    "directory": "./output_data_202308211911505128750_guest_9999_lr_0",
    "message": "download success, please check the path: ./output_data_202308211911505128750_guest_9999_lr_0"
}
```

## 3. More Documentation
- [Restful-api](https://github.com/FederatedAI/FATE-Flow/tree/v2.0.0-beta/doc/swagger/swagger.yaml)
- [CLI](https://github.com/FederatedAI/FATE-Client/tree/v2.0.0-beta/python/fate_client/flow_cli/build/doc)
- [Pipeline](https://github.com/FederatedAI/FATE/tree/v2.0.0-beta/doc/tutorial)
- [FATE Algorithms](https://github.com/FederatedAI/FATE/tree/v2.0.0-beta/doc/2.0/components)