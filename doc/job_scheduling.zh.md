# 多方联合作业

## 1. 说明

主要介绍如何使用`FATE Flow`联邦学习作业的定义

## 2. DAG定义
FATE 2.0采用全新DAG定义一个作业，包含各个组件的上下依赖关系

## 3. 作业功能配置
### 3.1 预测
```yaml
dag:
  conf:
    model_warehouse:                        
      model_id: '202307171452088269870'      
      model_version: '0'                    
```
在dag.conf.model_warehouse中定义预测任务依赖的模型信息，在算法中将使用此模型进行预测

### 3.2 job继承
```yaml
dag:
  conf:
    inheritance:                  
      job_id: "202307041704214920920"  
      task_list: ["reader_0"]         
```
在job.conf.inheritance中填入需要继承的job和算法组件名，新启动的job将直接复用这些组件的输出

### 3.3 指定调度方
```yaml
dag:
  conf:
    scheduler_party_id: "9999"   
```
在job.conf.scheduler_party_id中可指定调度方信息，若不指定则由发起方充当调度方

### 3.4 指定作业优先级
```yaml
dag:
  conf:
    priority: 2
```
在job.conf.priority中指定任务的调度权重，数值越大，优先级越高

### 3.5 失败自动重试

```yaml
dag:
  conf:
    auto_retries: 2
```
在job.conf.auto_retries中指定任务失败重试次数，默认为0。

### 3.6 资源数
```yaml
dag:
  conf:
    cores: 4
  task:
    engine_run:
      cores: 2
```
- 其中, dag.conf.cores为整个job的分配资源数(job_cores)，dag.conf.engine_run.cores为task的分配资源数(task_cores)。若以此配置启动job，其最大并行度为2。
- task并行度 = job_cores / task_cores

### 3.7 任务超时时间
```yaml
dag:
  task:
    timeout: 3600 # s
```
在dag.task.timeout中指定task的超时时间。当任务在达到超时时间还处于running状态时，会触发自动kill job操作

### 3.8 任务provider
```yaml
dag:
  task:
    provider: fate:2.0.1@local
```
在dag.task.provider中指定task的算法提供者、版本号和运行模式

## 4. 输入
**描述** 上游输入，分为两种输入类型，分别是数据和模型。

### 4.1 数据输入
- 作为组件的参数输入
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
reader组件支持直接传入某份fate数据表作为job级的数据输入。

- 某个组件输入另外一个组件的输出
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
binning_0依赖scale_0的输出数据train_output_data

### 4.2 模型输入
- model warehouse
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


## 5. 输出
作业的输出包括数据、模型和指标
### 5.1 输出指标
#### 查询指标
查询输出指标命令：
```shell
flow output query-metric -j $job_id -r $role -p $party_id -tn $task_name
```
- `flow output query-metric -j 202308211911505128750 -r arbiter -p 9998 -tn lr_0`
- 输入内容如下
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


### 5.2 输出模型
#### 查询模型
```shell
flow output query-model -j $job_id -r $role -p $party_id -tn $task_name
```
- `flow output query-model -j 202308211911505128750 -r host -p 9998 -tn lr_0`
- 查询结果如下：
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

#### 下载模型
```shell 
flow output download-model -j $job_id -r $role -p $party_id -tn $task_name -o $download_dir
```
- `flow output download-model -j 202308211911505128750 -r host -p 9998 -tn lr_0 -o ./`
- 下载结果如下：
```json
{
    "code": 0,
    "directory": "./output_model_202308211911505128750_host_9998_lr_0",
    "message": "download success, please check the path: ./output_model_202308211911505128750_host_9998_lr_0"
}


```


### 5.3 输出数据
#### 查询数据表
```shell
flow output query-data-table -j $job_id -r $role -p $party_id -tn $task_name
```
- `flow output query-data-table -j 202308211911505128750 -r host -p 9998 -tn binning_0`
- 查询结果如下：
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

#### 预览数据
```shell
flow output display-data -j $job_id -r $role -p $party_id -tn $task_name
```
- `flow output display-data -j 202308211911505128750 -r host -p 9998 -tn binning_0`

#### 下载数据
```shell
flow output download-data -j $job_id -r $role -p $party_id -tn $task_name -o $download_dir
```
- `flow output download-data -j 202308211911505128750 -r guest -p 9999 -tn lr_0 -o ./`
- 结果如下：
```json
{
    "code": 0,
    "directory": "./output_data_202308211911505128750_guest_9999_lr_0",
    "message": "download success, please check the path: ./output_data_202308211911505128750_guest_9999_lr_0"
}

```

