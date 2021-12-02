## Tracking

### metrics

获取某个组件任务产生的所有指标名称列表

```bash
flow tracking metrics [options]
```

**选项**

| 参数名                 | 必选 | 类型   | 说明                          |
| :--------------------- | :--- | :----- | ----------------------------- |
| -j, --job-id           | 是   | string | 作业id                        |
| -r, --role             | 是   | string | 参与角色                      |
| -p, --partyid          | 是   | string | 参与方id                      |
| -cpn, --component-name | 是   | string | 组件名，与job dsl中的保持一致 |

**返回**

| 参数名  | 类型   | 说明     |
| :------ | :----- | -------- |
| retcode | int    | 返回码   |
| retmsg  | string | 返回信息 |
| data    | dict   | 返回数据 |

**样例** 

```bash
flow tracking metrics -j 202111081618357358520 -r guest -p 9999 -cpn evaluation_0
```

输出:

```json
{
    "data": {
        "train": [
            "hetero_lr_0",
            "hetero_lr_0_ks_fpr",
            "hetero_lr_0_ks_tpr",
            "hetero_lr_0_lift",
            "hetero_lr_0_gain",
            "hetero_lr_0_accuracy",
            "hetero_lr_0_precision",
            "hetero_lr_0_recall",
            "hetero_lr_0_roc",
            "hetero_lr_0_confusion_mat",
            "hetero_lr_0_f1_score",
            "hetero_lr_0_quantile_pr"
        ]
    },
    "retcode": 0,
    "retmsg": "success"
}
```

### metric-all

获取组件任务的所有输出指标

```bash
flow tracking metric-all [options]
```

**选项**

| 参数名                 | 必选 | 类型   | 说明                          |
| :--------------------- | :--- | :----- | ----------------------------- |
| -j, --job-id           | 是   | string | 作业id                        |
| -r, --role             | 是   | string | 参与角色                      |
| -p, --partyid          | 是   | string | 参与方id                      |
| -cpn, --component-name | 是   | string | 组件名，与job dsl中的保持一致 |

**返回**

| 参数名  | 类型   | 说明     |
| :------ | :----- | -------- |
| retcode | int    | 返回码   |
| retmsg  | string | 返回信息 |
| data    | dict   | 返回数据 |
| jobId   | string | 作业id   |

**样例** 

```bash
flow tracking metric-all -j 202111081618357358520 -r guest -p 9999 -cpn evaluation_0
```

输出(篇幅有限，仅显示部分指标的数据且数组型数据中间省略了一些值):

```json
{
    "data": {
        "train": {
            "hetero_lr_0": {
                "data": [
                    [
                        "auc",
                        0.293893
                    ],
                    [
                        "ks",
                        0.0
                    ]
                ],
                "meta": {
                    "metric_type": "EVALUATION_SUMMARY",
                    "name": "hetero_lr_0"
                }
            },
            "hetero_lr_0_accuracy": {
                "data": [
                    [
                        0.0,
                        0.372583
                    ],
                    [
                        0.99,
                        0.616872
                    ]
                ],
                "meta": {
                    "curve_name": "hetero_lr_0",
                    "metric_type": "ACCURACY_EVALUATION",
                    "name": "hetero_lr_0_accuracy",
                    "thresholds": [
                        0.999471,
                        0.002577
                    ]
                }
            },
            "hetero_lr_0_confusion_mat": {
                "data": [],
                "meta": {
                    "fn": [
                        357,
                        0
                    ],
                    "fp": [
                        0,
                        212
                    ],
                    "metric_type": "CONFUSION_MAT",
                    "name": "hetero_lr_0_confusion_mat",
                    "thresholds": [
                        0.999471,
                        0.0
                    ],
                    "tn": [
                        212,
                        0
                    ],
                    "tp": [
                        0,
                        357
                    ]
                }
            }
        }
    },
    "retcode": 0,
    "retmsg": "success"
}
```

### parameters

提交作业后，系统依据job conf中的component_parameters结合系统默认组件参数，最终解析得到的实际组件任务运行参数

```bash
flow tracking parameters [options]
```

**选项**

| 参数名                 | 必选 | 类型   | 说明                          |
| :--------------------- | :--- | :----- | ----------------------------- |
| -j, --job-id           | 是   | string | 作业id                        |
| -r, --role             | 是   | string | 参与角色                      |
| -p, --partyid          | 是   | string | 参与方id                      |
| -cpn, --component-name | 是   | string | 组件名，与job dsl中的保持一致 |


**返回**

| 参数名  | 类型   | 说明     |
| :------ | :----- | -------- |
| retcode | int    | 返回码   |
| retmsg  | string | 返回信息 |
| data    | dict   | 返回数据 |
| jobId   | string | 作业id   |

**样例** 

```bash
flow tracking parameters  -j 202111081618357358520 -r guest -p 9999 -cpn hetero_lr_0
```

输出:

```json
{
    "data": {
        "ComponentParam": {
            "_feeded_deprecated_params": [],
            "_is_raw_conf": false,
            "_name": "HeteroLR#hetero_lr_0",
            "_user_feeded_params": [
                "batch_size",
                "penalty",
                "max_iter",
                "learning_rate",
                "init_param",
                "optimizer",
                "init_param.init_method",
                "alpha"
            ],
            "alpha": 0.01,
            "batch_size": 320,
            "callback_param": {
                "callbacks": [],
                "early_stopping_rounds": null,
                "metrics": [],
                "save_freq": 1,
                "use_first_metric_only": false,
                "validation_freqs": null
            },
            "cv_param": {
                "history_value_type": "score",
                "mode": "hetero",
                "n_splits": 5,
                "need_cv": false,
                "output_fold_history": true,
                "random_seed": 1,
                "role": "guest",
                "shuffle": true
            },
            "decay": 1,
            "decay_sqrt": true,
            "early_stop": "diff",
            "early_stopping_rounds": null,
            "encrypt_param": {
                "key_length": 1024,
                "method": "Paillier"
            },
            "encrypted_mode_calculator_param": {
                "mode": "strict",
                "re_encrypted_rate": 1
            },
            "floating_point_precision": 23,
            "init_param": {
                "fit_intercept": true,
                "init_const": 1,
                "init_method": "random_uniform",
                "random_seed": null
            },
            "learning_rate": 0.15,
            "max_iter": 3,
            "metrics": [
                "auc",
                "ks"
            ],
            "multi_class": "ovr",
            "optimizer": "rmsprop",
            "penalty": "L2",
            "predict_param": {
                "threshold": 0.5
            },
            "sqn_param": {
                "memory_M": 5,
                "random_seed": null,
                "sample_size": 5000,
                "update_interval_L": 3
            },
            "stepwise_param": {
                "direction": "both",
                "max_step": 10,
                "mode": "hetero",
                "need_stepwise": false,
                "nvmax": null,
                "nvmin": 2,
                "role": "guest",
                "score_name": "AIC"
            },
            "tol": 0.0001,
            "use_first_metric_only": false,
            "validation_freqs": null
        },
        "module": "HeteroLR"
    },
    "retcode": 0,
    "retmsg": "success"
}
```

### output-data

获取组件输出

```bash
flow tracking output-data [options]
```

**选项**

| 参数名                 | 必选 | 类型   | 说明                          |
| :--------------------- | :--- | :----- | ----------------------------- |
| -j, --job-id           | 是   | string | 作业id                        |
| -r, --role             | 是   | string | 参与角色                      |
| -p, --partyid          | 是   | string | 参与方id                      |
| -cpn, --component-name | 是   | string | 组件名，与job dsl中的保持一致 |
| -o, --output-path      | 是   | string | 输出数据的存放路径            |

**返回**

| 参数名  | 类型   | 说明     |
| :------ | :----- | -------- |
| retcode | int    | 返回码   |
| retmsg  | string | 返回信息 |
| data    | dict   | 返回数据 |
| jobId   | string | 作业id   |

**样例** 

```bash
flow tracking output-data  -j 202111081618357358520 -r guest -p 9999 -cpn hetero_lr_0 -o ./
```

输出:

```json
{
    "retcode": 0,
    "directory": "$FATE_PROJECT_BASE/job_202111081618357358520_hetero_lr_0_guest_9999_output_data",
    "retmsg": "Download successfully, please check $FATE_PROJECT_BASE/job_202111081618357358520_hetero_lr_0_guest_9999_output_data directory"
}
```

### output-data-table

获取组件的输出数据表名

```bash
flow tracking output-data-table [options]
```

**选项**

| 参数名                 | 必选 | 类型   | 说明                          |
| :--------------------- | :--- | :----- | ----------------------------- |
| -j, --job-id           | 是   | string | 作业id                        |
| -r, --role             | 是   | string | 参与角色                      |
| -p, --partyid          | 是   | string | 参与方id                      |
| -cpn, --component-name | 是   | string | 组件名，与job dsl中的保持一致 |

**返回**

| 参数名  | 类型   | 说明     |
| :------ | :----- | -------- |
| retcode | int    | 返回码   |
| retmsg  | string | 返回信息 |
| data    | dict   | 返回数据 |
| jobId   | string | 作业id   |

**样例** 

```bash
flow tracking output-data-table  -j 202111081618357358520 -r guest -p 9999 -cpn hetero_lr_0
```

输出:

```json
{
    "data": [
        {
            "data_name": "train",
            "table_name": "9688fa00406c11ecbd0bacde48001122",
            "table_namespace": "output_data_202111081618357358520_hetero_lr_0_0"
        }
    ],
    "retcode": 0,
    "retmsg": "success"
}
```

### output-model

获取某个组件任务的输出模型

```bash
flow tracking output-model [options]
```

**选项**

| 参数名                 | 必选 | 类型   | 说明                          |
| :--------------------- | :--- | :----- | ----------------------------- |
| -j, --job-id           | 是   | string | 作业id                        |
| -r, --role             | 是   | string | 参与角色                      |
| -p, --partyid          | 是   | string | 参与方id                      |
| -cpn, --component-name | 是   | string | 组件名，与job dsl中的保持一致 |

**返回**

| 参数名  | 类型   | 说明     |
| :------ | :----- | -------- |
| retcode | int    | 返回码   |
| retmsg  | string | 返回信息 |
| data    | dict   | 返回数据 |
| jobId   | string | 作业id   |

**样例** 

```bash
flow tracking output-model  -j 202111081618357358520 -r guest -p 9999 -cpn hetero_lr_0
```

输出:

```json
{
    "data": {
        "bestIteration": -1,
        "encryptedWeight": {},
        "header": [
            "x0",
            "x1",
            "x2",
            "x3",
            "x4",
            "x5",
            "x6",
            "x7",
            "x8",
            "x9"
        ],
        "intercept": 0.24451607054764884,
        "isConverged": false,
        "iters": 3,
        "lossHistory": [],
        "needOneVsRest": false,
        "weight": {
            "x0": 0.04639947589856569,
            "x1": 0.19899685467216902,
            "x2": -0.18133550931649306,
            "x3": 0.44928868756862206,
            "x4": 0.05285905125502288,
            "x5": 0.319187932844076,
            "x6": 0.42578983446194013,
            "x7": -0.025765956309895477,
            "x8": -0.3699194462271593,
            "x9": -0.1212094750908295
        }
    },
    "meta": {
        "meta_data": {
            "alpha": 0.01,
            "batchSize": "320",
            "earlyStop": "diff",
            "fitIntercept": true,
            "learningRate": 0.15,
            "maxIter": "3",
            "needOneVsRest": false,
            "optimizer": "rmsprop",
            "partyWeight": 0.0,
            "penalty": "L2",
            "reEncryptBatches": "0",
            "revealStrategy": "",
            "tol": 0.0001
        },
        "module_name": "HeteroLR"
    },
    "retcode": 0,
    "retmsg": "success"
}
```

### get-summary

每个组件允许设置一些摘要信息，便于观察分析

```bash
flow tracking get-summary [options]
```

**选项**

| 参数名                 | 必选 | 类型   | 说明                          |
| :--------------------- | :--- | :----- | ----------------------------- |
| -j, --job-id           | 是   | string | 作业id                        |
| -r, --role             | 是   | string | 参与角色                      |
| -p, --partyid          | 是   | string | 参与方id                      |
| -cpn, --component-name | 是   | string | 组件名，与job dsl中的保持一致 |

**返回**

| 参数名  | 类型   | 说明     |
| :------ | :----- | -------- |
| retcode | int    | 返回码   |
| retmsg  | string | 返回信息 |
| data    | dict   | 返回数据 |
| jobId   | string | 作业id   |

**样例** 

```bash
flow tracking get-summary -j 202111081618357358520 -r guest -p 9999 -cpn hetero_lr_0
```

输出:

```json
{
    "data": {
        "best_iteration": -1,
        "coef": {
            "x0": 0.04639947589856569,
            "x1": 0.19899685467216902,
            "x2": -0.18133550931649306,
            "x3": 0.44928868756862206,
            "x4": 0.05285905125502288,
            "x5": 0.319187932844076,
            "x6": 0.42578983446194013,
            "x7": -0.025765956309895477,
            "x8": -0.3699194462271593,
            "x9": -0.1212094750908295
        },
        "intercept": 0.24451607054764884,
        "is_converged": false,
        "one_vs_rest": false
    },
    "retcode": 0,
    "retmsg": "success"
}
```

### tracking-source

用于查询某张表的父表及源表

```bash
flow table tracking-source [options]
```

**选项**

| 参数名    | 必选 | 类型   | 说明           |
| :-------- | :--- | :----- | -------------- |
| name      | 是   | string | fate表名       |
| namespace | 是   | string | fate表命名空间 |

**返回**

| 参数名  | 类型   | 说明     |
| :------ | :----- | -------- |
| retcode | int    | 返回码   |
| retmsg  | string | 返回信息 |
| data    | object | 返回数据 |

**样例**

```json
{
    "data": [{"parent_table_name": "61210fa23c8d11ec849a5254004fdc71", "parent_table_namespace": "output_data_202111031759294631020_hetero_lr_0_0", "source_table_name": "breast_hetero_guest", "source_table_namespace": "experiment"}],
    "retcode": 0,
    "retmsg": "success"
}
```

### tracking-job

用于查询某张表的使用情况

```bash
flow table tracking-job [options]
```

**选项**

| 参数名    | 必选 | 类型   | 说明           |
| :-------- | :--- | :----- | -------------- |
| name      | 是   | string | fate表名       |
| namespace | 是   | string | fate表命名空间 |

**返回**

| 参数名  | 类型   | 说明     |
| :------ | :----- | -------- |
| retcode | int    | 返回码   |
| retmsg  | string | 返回信息 |
| data    | object | 返回数据 |

**样例**

```json
{
    "data": {"count":2,"job":["202111052115375327830", "202111031816501123160"]},
    "retcode": 0,
    "retmsg": "success"
}
```
