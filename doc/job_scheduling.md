# Multi-Party Joint Operation

## 1. Introduction

This primarily introduces how to define federated learning jobs using `FATE Flow`.

## 2. DAG Definition

FATE 2.0 uses a brand new DAG to define a job, including the upstream and downstream dependencies of each component.

## 3. Job Functional Configuration

### 3.1 Prediction
```yaml
dag:
  conf:
    model_warehouse:                        
      model_id: '202307171452088269870'      
      model_version: '0'                    
```
In `dag.conf.model_warehouse`, define the model information that the prediction task relies on. This model will be used for prediction in the algorithm.

### 3.2 Job Inheritance
```yaml
dag:
  conf:
    inheritance:                  
      job_id: "202307041704214920920"  
      task_list: ["reader_0"]         
```
In `job.conf.inheritance`, fill in the job and algorithm component names that need to be inherited. The newly started job will directly reuse the outputs of these components.

### 3.3 Specifying the Scheduler Party
```yaml
dag:
  conf:
    scheduler_party_id: "9999"   
```
In `job.conf.scheduler_party_id`, you can specify scheduler party information. If not specified, the initiator acts as the scheduler.

### 3.4 Specifying Job Priority
```yaml
dag:
  conf:
    priority: 2
```
In `job.conf.priority`, specify the scheduling weight of the task. The higher the value, the higher the priority.

### 3.5 Automatic Retry on Failure
```yaml
dag:
  conf:
    auto_retries: 2
```
In `job.conf.auto_retries`, specify the number of retries if a task fails. Default is 0.

### 3.6 Resource Allocation
```yaml
dag:
  conf:
    cores: 4
  task:
    engine_run:
      cores: 2
```
- Here, `dag.conf.cores` represents the allocated resources for the entire job (`job_cores`), and `dag.conf.engine_run.cores` represents the allocated resources for the task (`task_cores`). If a job is started with this configuration, its maximum parallelism will be 2.
- Task parallelism = job_cores / task_cores

### 3.7 Task Timeout
```yaml
dag:
  task:
    timeout: 3600 # s
```
In `dag.task.timeout`, specify the task's timeout. When a task is in the 'running' state after reaching the timeout, it triggers an automatic job kill operation.

### 3.8 Task Provider
```yaml
dag:
  task:
    provider: fate:2.0.1@local
```
In `dag.task.provider`, specify the algorithm provider, version number, and execution mode for the task.

## 4. Input
**Description:** Upstream input, divided into two input types: data and models.

### 4.1 Data Input
- As parameter input to a component
```yaml
dag:
  party_tasks:
    guest_9999:
      tasks:
        reader_0:
          parameters:
            name: breast_hetero_guest
            namespace: experiment
    host_9998:
      tasks:
        reader_0:
          parameters:
            name: breast_hetero_host
            namespace: experiment
```
The `reader` component supports directly passing a FATE data table as job-level data input.

- Input of one component from another component's output
```yaml
dag:
  tasks:
    binning_0:
      component_ref: hetero_feature_binning
      inputs:
        data:
          train_data:
            task_output_artifact:
              output_artifact_key: train_output_data
              producer_task: scale_0
```
`binning_0` depends on the output data of `scale_0`.

### 4.2 Model Input
- Model Warehouse
```yaml
dag:
  conf:
    model_warehouse:                        
      model_id: '202307171452088269870'      
      model_version: '0'  
  tasks:
    selection_0:
      component_ref: hetero_feature_selection
      dependent_tasks:
      - scale_0
        model:
          input_model:
            model_warehouse:
              output_artifact_key: train_output_model
              producer_task: selection_0
```

## 5. Output
The job's output includes data, models, and metrics.

### 5.1 Metric Output
#### Querying Metrics
Querying output metrics command:
```shell
flow output query-metric -j $job_id -r $role -p $party_id -tn $task_name
```
- `flow output query-metric -j 202308211911505128750 -r arbiter -p 9998 -tn lr_0`
- Input content as follows:
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


### 5.2 Model Output
#### Querying Models
```shell
flow output query-model -j $job_id -r $role -p $party_id -tn $task_name
```
- `flow output query-model -j 202308211911505128750 -r host -p 9998 -tn lr_0`
- Query result as follows:
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

#### Downloading Models
```shell 
flow output download-model -j $job_id -r $role -p $party_id -tn $task_name -o $download_dir
```
- `flow output download-model -j 202308211911505128750 -r host -p 9998 -tn lr_0 -o ./`
- Download result:
```json
{
    "code": 0,
    "directory": "./output_model_202308211911505128750_host_9998_lr_0",
    "message": "Download success, please check the path: ./output_model_202308211911505128750_host_9998_lr_0"
}
```

### 5.3 Output Data
#### Querying Data Tables
```shell
flow output query-data-table -j $job_id -r $role -p $party_id -tn $task_name
```
- `flow output query-data-table -j 202308211911505128750 -r host -p 9998 -tn binning_0`
- Query result:
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

#### Previewing Data
```shell
flow output display-data -j $job_id -r $role -p $party_id -tn $task_name
```
- `flow output display-data -j 202308211911505128750 -r host -p 9998 -tn binning_0`

#### Downloading Data
```shell
flow output download-data -j $job_id -r $role -p $party_id -tn $task_name -o $download_dir
```
- `flow output download-data -j 202308211911505128750 -r guest -p 9999 -tn lr_0 -o ./`
- Result:
```json
{
    "code": 0,
    "directory": "./output_data_202308211911505128750_guest_9999_lr_0",
    "message": "Download success, please check the path: ./output_data_202308211911505128750_guest_9999_lr_0"
}
```

