## 快速入门

### 1. 环境部署
##### 1.1 源码部署
##### 1.2 单机版部署
##### 1.3 集群部署

### 2. 使用指南
fate提供的客户端包括SDK、CLI和Pipeline，若你的环境中没有部署FATE Client,可以使用`pip install fate_client==2.0.0.beta`下载。以下的使用操作均基于cli编写，你也可以通过SDK或者Pipeline中找到对应的操作接口。
#### 2.1 数据上传
在2.0-beta版本中，数据上传分为两步：
- upload: 将数据上传到FATE支持存储服务中 
- transformer: 将数据转化成dataframe
##### 2.1.1 upload
##### 2.1.1.1 配置及数据
 - 上传配置位于[examples-upload](../examples/upload)，上传数据位于[upload-data](../examples/data)
 - 你也可以使用自己的数据，并修改upload配置中的"meta"信息。
##### 2.1.1.2 上传guest方数据
```shell
flow data upload -c examples/upload/upload_guest.json
```
- 需要记录返回的name和namespace，作为transformer的参数。
##### 2.1.1.3 上传host方数据
```shell
flow data upload -c examples/upload/upload_host.json
```
- 需要记录返回的name和namespace，作为transformer的参数。
##### 2.1.1.4 上传结果
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
其中"namespace"和"name"是这份数据在fate中的标识，以便下面后续transformer阶段使用时可直接引用。

##### 2.1.1.5 数据查询
因为upload为异步操作，需要确认是否上传成功才可进行后续操作。
```shell
flow table query --namespace upload --name 36491bc8-3fef-11ee-be05-16b977118319
```
上传成功信息如下：
```json
{
    "code": 0,
    "data": {
        "count": 569,
        "data_type": "table",
        "engine": "standalone",
        "meta": {
            "delimiter": ",",
            "dtype": "'float32",
            "header": "extend_sid,id,x0,x1,x2,x3,x4,x5,x6,x7,x8,x9,x10,x11,x12,x13,x14,x15,x16,x17,x18,x19",
            "input_format": "dense",
            "label_type": "int",
            "match_id_name": "id",
            "match_id_range": 0,
            "sample_id_name": "extend_sid",
            "tag_value_delimiter": ":",
            "tag_with_value": false,
            "weight_type": "float32"
        },
        "name": "36491bc8-3fef-11ee-be05-16b977118319",
        "namespace": "upload",
        "path": "xxx",
        "source": {
            "component": "upload",
            "output_artifact_key": "data",
            "output_index": null,
            "party_task_id": "",
            "task_id": "",
            "task_name": "upload"
        }
    },
    "message": "success"
}

```
若返回的code为0即为上传成功。

##### 2.1.2 transformer
##### 2.1.2.1 配置
 - transformer配置位于[examples-transformer](../examples/transformer)
##### 2.1.2.2 transformer guest
- 配置路径位于： examples/transformer/transformer_guest.json
- 修改配置中"data_warehouse"的"namespace"和"name"：上面upload guest阶段的输出
```shell
flow data transformer -c examples/transformer/transformer_guest.json
```
##### 2.1.2.3 transformer host
- 配置路径位于： examples/transformer/transformer_host.json
- 修改配置中"data_warehouse"的"namespace"和"name"：上面upload host阶段的输出
```shell
flow data transformer -c examples/transformer/transformer_host.json
```
##### 2.1.2.4 transformer结果
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
其中"namespace"和"name"是这份数据在fate中的标识，后续建模作业中使用。

##### 2.1.2.5 查看数据是否上传成功

因为transformer也是异步操作，需要确认是否上传成功才可进行后续操作。
```shell
flow table query --namespace experiment  --name breast_hetero_guest
```
```shell
flow table query --namespace experiment  --name breast_hetero_host
```
若返回的code为0即为上传成功。

#### 2.2 开始FATE作业
##### 2.2.1 提交作业
当你的数据准备好后，可以开始提交作业给FATE Flow：
- 训练job配置example位于[lr-train](../examples/lr/train_lr.yaml);
- 预测job配置example位于[lr-predict](../examples/lr/predict_lr.yaml);预测任务需要修改"dag.conf.model_warehouse"成训练作业的输出模型。
- 训练和预测job配置中站点id为"9998"和"9999"。如果你的部署环境为集群版，需要替换成真实的站点id；单机版可使用默认配置。
- 如果想要使用自己的数据，可以更改配置中guest和host的data_warehouse的namespace和name
- 提交作业的命令为:
```shell
flow job submit -c examples/lr/train_lr.yaml 
```
- 提交成功返回结果:
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
这里的"data"内容即为该作业的输出模型。

##### 2.2.2 查询作业
在作业的运行过程时，你可以通过查询命令获取作业的运行状态
```shell
flow job query -j $job_id
```

##### 2.2.3 停止作业
在作业的运行过程时，你可以通过停止作业命令来终止当前作业
```shell
flow job stop -j $job_id
```

##### 2.2.4 重跑作业
在作业的运行过程时，如果运行失败，你可以通过重跑命令来重跑当前作业
```shell
flow job rerun -j $job_id
```

#### 2.3 获取作业输出结果
作业的输出包括数据、模型和指标
##### 2.3.1 输出指标
查询输出指标命令：
```shell
flow output query-metric -j $job_id -r $role -p $party_id -tn $task_name
```
如使用上面的训练dag提交任务，可以使用`flow output query-metric -j 202308211911505128750 -r arbiter -p 9998 -tn lr_0`查询。
查询结果如下:
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


##### 2.3.2 输出模型
###### 2.3.2.1 查询模型
```shell
flow output query-model -j $job_id -r $role -p $party_id -tn $task_name
```
如使用上面的训练dag提交任务，可以使用`flow output query-model -j 202308211911505128750 -r host -p 9998 -tn lr_0`查询。
查询结果如下：
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

###### 2.3.2.2 下载模型
```shell 
flow output download-model -j $job_id -r $role -p $party_id -tn $task_name -o $download_dir
```
如使用上面的训练dag提交任务，可以使用`flow output download-model -j 202308211911505128750 -r host -p 9998 -tn lr_0 -o ./`下载。
下载结果如下：
```json
{
    "code": 0,
    "directory": "./output_model_202308211911505128750_host_9998_lr_0",
    "message": "download success, please check the path: ./output_model_202308211911505128750_host_9998_lr_0"
}


```


##### 2.3.3 输出数据
###### 2.3.3.1 查询数据表
```shell
flow output query-data-table -j $job_id -r $role -p $party_id -tn $task_name
```
如使用上面的训练dag提交任务，可以使用`flow output query-data-table -j 202308211911505128750 -r host -p 9998 -tn binning_0`查询。
查询结果如下：
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

###### 2.3.3.2 预览数据
```shell
flow output display-data -j $job_id -r $role -p $party_id -tn $task_name
```
如使用上面的训练dag提交任务，可以使用`flow output display-data -j 202308211911505128750 -r host -p 9998 -tn binning_0`预览输出数据。

###### 2.3.3.3 下载数据
```shell
flow output download-data -j $job_id -r $role -p $party_id -tn $task_name -o $download_dir
```
如使用上面的训练dag提交任务，可以使用`flow output download-data -j 202308211911505128750 -r guest -p 9999 -tn lr_0 -o ./`下载输出数据。
下载结果如下：
```json
{
    "code": 0,
    "directory": "./output_data_202308211911505128750_guest_9999_lr_0",
    "message": "download success, please check the path: ./output_data_202308211911505128750_guest_9999_lr_0"
}

```
