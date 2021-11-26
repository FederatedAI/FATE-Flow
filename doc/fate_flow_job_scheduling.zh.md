# 多方联合作业&任务调度

## 1. 说明

主要介绍如何使用`FATE Flow`提交一个联邦学习作业，并观察使用

## 2. 作业提交

- 构建一个联邦学习作业，并提交到调度系统执行
- 需要两个配置文件：job dsl和job conf
- job dsl配置运行的组件：列表、输入输出关系
- job conf配置组件执行参数、系统运行参数

{{snippet('cli/job.zh.md', '### submit')}}

## 3. Job DSL配置说明

DSL 的配置文件采用 json 格式，实际上，整个配置文件就是一个 json 对象 （dict）。

### 3.1 组件列表

**描述** 在这个 dict 的第一级是 `components`，用来表示这个任务将会使用到的各个模块。
**样例**

```json
{
  "components" : {
          ...
      }
}
```

每个独立的模块定义在 "components" 之下，例如：

```json
"data_transform_0": {
      "module": "DataTransform",
      "input": {
          "data": {
              "data": [
                  "reader_0.train_data"
              ]
          }
      },
      "output": {
          "data": ["train"],
          "model": ["model"]
      }
  }
```

所有数据需要通过**Reader**模块从数据存储拿取数据，注意此模块仅有输出`output`

```json
"reader_0": {
      "module": "Reader",
      "output": {
          "data": ["train"]
      }
}
```

### 3.2 模块

**描述** 用来指定使用的组件，所有可选module名称参考：
**样例**

```json
"hetero_feature_binning_1": {
    "module": "HeteroFeatureBinning",
     ...
}
```

### 3.3 输入

**描述** 上游输入，分为两种输入类型，分别是数据和模型。

#### 数据输入

**描述** 上游数据输入，分为三种输入类型：
    
    > 1.  data: 一般被用于 data-transform模块, feature_engineering 模块或者
    >     evaluation 模块
    > 2.  train_data: 一般被用于 homo_lr, hetero_lr 和 secure_boost
    >     模块。如果出现了 train_data 字段，那么这个任务将会被识别为一个 fit 任务
    > 3.  validate_data： 如果存在 train_data
    >     字段，那么该字段是可选的。如果选择保留该字段，则指向的数据将会作为
    >     validation set
    > 4.  test_data: 用作预测数据，如提供，需同时提供model输入。

#### 模型输入

**描述** 上游模型输入，分为两种输入类型：
    1.  model: 用于同种类型组件的模型输入。例如，hetero_binning_0 会对模型进行 fit，然后
        hetero_binning_1 将会使用 hetero_binning_0 的输出用于 predict 或
        transform。代码示例：

```json
        "hetero_feature_binning_1": {
            "module": "HeteroFeatureBinning",
            "input": {
                "data": {
                    "data": [
                        "data_transform_1.validate_data"
                    ]
                },
                "model": [
                    "hetero_feature_binning_0.fit_model"
                ]
            },
            "output": {
                "data": ["validate_data"],
              "model": ["eval_model"]
            }
        }
```
    2.  isometric_model: 用于指定继承上游组件的模型输入。 例如，feature selection 的上游组件是
        feature binning，它将会用到 feature binning 的信息来作为 feature
        importance。代码示例：
```json
        "hetero_feature_selection_0": {
            "module": "HeteroFeatureSelection",
            "input": {
                "data": {
                    "data": [
                        "hetero_feature_binning_0.train"
                    ]
                },
                "isometric_model": [
                    "hetero_feature_binning_0.output_model"
                ]
            },
            "output": {
                "data": ["train"],
                "model": ["output_model"]
            }
        }
```

### 3.4 输出

**描述** 输出，与输入一样，分为数据和模型输出

#### 数据输出

**描述** 数据输出，分为四种输出类型：

1.  data: 常规模块数据输出
2.  train_data: 仅用于Data Split
3.  validate_data: 仅用于Data Split
4.  test_data： 仅用于Data Split

#### 模型输出

**描述** 模型输出，仅使用model

### 3.5 组件Provider

FATE-Flow 1.7.0版本开始，同一个FATE-Flow系统支持加载多种且多版本的组件提供方，也即provider，provider提供了若干个组件，提交作业时可以配置组件的来源provider

**描述** 指定provider，支持全局指定以及单个组件指定；若不指定，默认 provider：`fate@$FATE_VERSION`

**格式** `provider_name@$provider_version`

**进阶** 可以通过组件注册CLI注册新的 provider，目前支持的 provider：fate 和 fate_sql，具体请参考[FATE Flow 组件中心](./fate_flow_component_registry.zh.md)

**样例**

```json
{
  "provider": "fate@1.7.0",
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
      "provider": "fate@1.7.0",
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
      "need_deploy": true
    },
    "hetero_feature_binning_0": {
      "module": "HeteroFeatureBinning",
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
        ],
        "model": [
          "hetero_feature_binning"
        ]
      }
    }
  }
}
```

## 4. Job Conf配置说明

Job Conf用于设置各个参与方的信息, 作业的参数及各个组件的参数。 内容包括如下：

### 4.1 DSL版本

**描述** 配置版本，默认不配置为1，建议配置为2
**样例**
```json
"dsl_version": "2"
```

### 4.2 作业参与方

#### 发起方

**描述** 任务发起方的role和party_id。
**样例**
```json
"initiator": {
    "role": "guest",
    "party_id": 9999
}
```

#### 所有参与方

**描述** 各参与方的信息。
**说明** 在 role 字段中，每一个元素代表一种角色以及承担这个角色的 party_id。每个角色的 party_id
    以列表形式存在，因为一个任务可能涉及到多个 party 担任同一种角色。
**样例**

```json
"role": {
    "guest": [9999],
    "host": [10000],
    "arbiter": [10000]
}
```

### 4.3 系统运行参数

**描述**
    配置作业运行时的主要系统参数

#### 参数应用范围策略设置

**应用于所有参与方，使用common范围标识符
**仅应用于某参与方，使用role范围标识符，使用(role:)party_index定位被指定的参与方，直接指定的参数优先级高于common参数

```json
"common": {
}

"role": {
  "guest": {
    "0": {
    }
  }
}
```

其中common下的参数应用于所有参与方，role-guest-0配置下的参数应用于guest角色0号下标的参与方
注意，当前版本系统运行参数未对仅应用于某参与方做严格测试，建议使用优先选用common

#### 支持的系统参数

| 配置项                        | 默认值                | 支持值                          | 说明                                                                                              |
| ----------------------------- | --------------------- | ------------------------------- | ------------------------------------------------------------------------------------------------- |
| job_type                      | train                 | train, predict                  | 任务类型                                                                                          |
| task_cores                    | 4                     | 正整数                          | 作业申请的总cpu核数                                                                               |
| task_parallelism              | 1                     | 正整数                          | task并行度                                                                                        |
| computing_partitions          | task所分配到的cpu核数 | 正整数                          | 计算时数据表的分区数                                                                              |
| eggroll_run                   | 无                    | processors_per_node等           | eggroll计算引擎相关配置参数，一般无须配置，由task_cores自动计算得到，若配置则task_cores参数不生效 |
| spark_run                     | 无                    | num-executors, executor-cores等 | spark计算引擎相关配置参数，一般无须配置，由task_cores自动计算得到，若配置则task_cores参数不生效   |
| rabbitmq_run                  | 无                    | queue, exchange等               | rabbitmq创建queue、exchange的相关配置参数，一般无须配置，采取系统默认值                           |
| pulsar_run                    | 无                    | producer, consumer等            | pulsar创建producer和consumer时候的相关配置，一般无需配置。                                        |
| federated_status_collect_type | PUSH                  | PUSH, PULL                      | 多方运行状态收集模式，PUSH表示每个参与方主动上报到发起方，PULL表示发起方定期向各个参与方拉取      |
| timeout                       | 259200 (3天)          | 正整数                          | 任务超时时间,单位秒                                                                               |
| audo_retries                  | 3                     | 正整数                          | 每个任务失败自动重试最大次数                                                                      |
| model_id                      | \-                    | \-                              | 模型id，预测任务需要填入                                                                          |
| model_version                 | \-                    | \-                              | 模型version，预测任务需要填入                                                                     |

1. 计算引擎和存储引擎之间具有一定的支持依赖关系
2. 开发者可自行实现适配的引擎，并在runtime config配置引擎

#### 参考配置

1.  无须关注计算引擎，采取系统默认cpu分配计算策略时的配置

```json
"job_parameters": {
  "common": {
    "job_type": "train",
    "task_cores": 6,
    "task_parallelism": 2,
    "computing_partitions": 8,
    "timeout": 36000
  }
}
```

2.  使用eggroll作为computing engine，采取直接指定cpu等参数时的配置

```json
"job_parameters": {
  "common": {
    "job_type": "train",
    "eggroll_run": {
      "eggroll.session.processors.per.node": 2
    },
    "task_parallelism": 2,
    "computing_partitions": 8,
    "timeout": 36000,
  }
}
```

3.  使用spark作为computing engine，rabbitmq作为federation engine,采取直接指定cpu等参数时的配置

```json
"job_parameters": {
  "common": {
    "job_type": "train",
    "spark_run": {
      "num-executors": 1,
      "executor-cores": 2
    },
    "task_parallelism": 2,
    "computing_partitions": 8,
    "timeout": 36000,
    "rabbitmq_run": {
      "queue": {
        "durable": true
      },
      "connection": {
        "heartbeat": 10000
      }
    }
  }
}
```

4.  使用spark作为computing engine，pulsar作为federation engine

```json
"job_parameters": {
  "common": {
    "spark_run": {
      "num-executors": 1,
      "executor-cores": 2
    },
  }
}
```
更多资源相关高级配置请参考[资源管理](#4-资源管理)

### 4.3 组件运行参数

#### 参数应用范围策略设置

- 应用于所有参与方，使用common范围标识符
- 仅应用于某参与方，使用role范围标识符，使用(role:)party_index定位被指定的参与方，直接指定的参数优先级高于common参数

```json
"commom": {
}

"role": {
  "guest": {
    "0": {
    }
  }
}
```

其中common配置下的参数应用于所有参与方，role-guest-0配置下的参数表示应用于guest角色0号下标的参与方
注意，当前版本组件运行参数已支持两种应用范围策略

#### 参考配置

- `intersection_0`与`hetero_lr_0`两个组件的运行参数，放在common范围下，应用于所有参与方
- 对于`reader_0`与`data_transform_0`两个组件的运行参数，依据不同的参与方进行特定配置，这是因为通常不同参与方的输入参数并不一致，所有通常这两个组件一般按参与方设置
- 上述组件名称是在DSL配置文件中定义

```json
"component_parameters": {
  "common": {
    "intersection_0": {
      "intersect_method": "raw",
      "sync_intersect_ids": true,
      "only_output_key": false
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
          "table": {"name": "breast_hetero_guest", "namespace": "experiment"}
        },
        "data_transform_0":{
          "with_label": true,
          "label_name": "y",
          "label_type": "int",
          "output_format": "dense"
        }
      }
    },
    "host": {
      "0": {
        "reader_0": {
          "table": {"name": "breast_hetero_host", "namespace": "experiment"}
        },
        "data_transform_0":{
          "with_label": false,
          "output_format": "dense"
        }
      }
    }
  }
}
```

## 5. 多Host 配置

多Host任务应在role下列举所有host信息

**样例**:

```json
"role": {
   "guest": [
     10000
   ],
   "host": [
     10000, 10001, 10002
   ],
   "arbiter": [
     10000
   ]
}
```

各host不同的配置应在各自对应模块下分别列举

**样例**:

```json
"component_parameters": {
   "role": {
      "host": {
         "0": {
            "reader_0": {
               "table":
                {
                  "name": "hetero_breast_host_0",
                  "namespace": "hetero_breast_host"
                }
            }
         },
         "1": {
            "reader_0": {
               "table":
               {
                  "name": "hetero_breast_host_1",
                  "namespace": "hetero_breast_host"
               }
            }
         },
         "2": {
            "reader_0": {
               "table":
               {
                  "name": "hetero_breast_host_2",
                  "namespace": "hetero_breast_host"
               }
            }
         }
      }
   }
}
```

## 6. 预测任务配置

### 6.1 说明

DSL V2不会自动为训练任务生成预测dsl。 用户需要首先使用`Flow Client`部署所需模型中模块。
详细命令说明请参考[fate_flow_client](./fate_flow_client.zh.md)

```bash
flow model deploy --model-id $model_id --model-version $model_version --cpn-list ...
```

可选地，用户可以在预测dsl中加入新模块，如`Evaluation`

### 6.2 样例

训练 dsl：

```json
"components": {
    "reader_0": {
        "module": "Reader",
        "output": {
            "data": [
                "data"
            ]
        }
    },
    "data_transform_0": {
        "module": "DataTransform",
        "input": {
            "data": {
                "data": [
                    "reader_0.data"
                ]
            }
        },
        "output": {
            "data": [
                "data"
            ],
            "model": [
                "model"
            ]
        }
    },
    "intersection_0": {
        "module": "Intersection",
        "input": {
            "data": {
                "data": [
                    "data_transform_0.data"
                ]
            }
        },
        "output": {
            "data":[
                "data"
            ]
        }
    },
    "hetero_nn_0": {
        "module": "HeteroNN",
        "input": {
            "data": {
                "train_data": [
                    "intersection_0.data"
                ]
            }
        },
        "output": {
            "data": [
                "data"
            ],
            "model": [
                "model"
            ]
        }
    }
}
```

预测 dsl:

```json
"components": {
    "reader_0": {
        "module": "Reader",
        "output": {
            "data": [
                "data"
            ]
        }
    },
    "data_transform_0": {
        "module": "DataTransform",
        "input": {
            "data": {
                "data": [
                    "reader_0.data"
                ]
            }
        },
        "output": {
            "data": [
                "data"
            ],
            "model": [
                "model"
            ]
        }
    },
    "intersection_0": {
        "module": "Intersection",
        "input": {
            "data": {
                "data": [
                    "data_transform_0.data"
                ]
            }
        },
        "output": {
            "data":[
                "data"
            ]
        }
    },
    "hetero_nn_0": {
        "module": "HeteroNN",
        "input": {
            "data": {
                "train_data": [
                    "intersection_0.data"
                ]
            }
        },
        "output": {
            "data": [
                "data"
            ],
            "model": [
                "model"
            ]
        }
    },
    "evaluation_0": {
        "module": "Evaluation",
        "input": {
            "data": {
                "data": [
                    "hetero_nn_0.data"
                ]
            }
         },
         "output": {
             "data": [
                 "data"
             ]
          }
    }
}
```

## 7. 作业重跑

`1.5.0`版本, 开始支持重跑某个作业, 但是仅支持失败的作业
`1.7.0`版本支持成功的作业重跑, 并且可以指定从哪个组件开始重跑, 被指定的组件及其下游组件会重跑, 但其他组件不会重跑

{{snippet('cli/job.zh.md', '### rerun')}}

## 8. 作业参数更新

实际生产建模过程中, 需要进行不断调试修改组件参数且重跑, 但是此时并不是所有组件都需要调整并且重跑, 因此在`1.7.0`版本后支持修改某个组件的参数更新, 且配合`rerun`命令按需重跑

{{snippet('cli/job.zh.md', '### parameter-update')}}

## 9. 作业调度策略

- 按提交时间先后入队
- 目前仅支持FIFO策略，也即每次调度器仅会扫描第一个作业，若第一个作业申请资源成功则start且出队，若申请资源失败则等待下一轮调度

## 10. 依赖分发

**简要描述：** 

- 支持从client节点分发fate和python依赖;
- work节点不用部署fate;
- 当前版本只有fate on spark支持分发模式;

**相关参数配置**:

conf/service_conf.yaml:

```yaml
dependent_distribution: true
```

fate_flow/settings.py

```python
FATE_FLOW_UPDATE_CHECK = False
```

**说明：**

- dependent_distribution: 依赖分发开关;，默认关闭;关闭时需要在每个work节点部署fate, 另外还需要在spark的配置spark-env.sh中填配置PYSPARK_DRIVER_PYTHON和PYSPARK_PYTHON；

- FATE_FLOW_UPDATE_CHECK: 依赖校验开关, 默认关闭;打开后每次提交任务都会自动校验fate代码是否发生改变;若发生改变则会重新上传fate代码依赖;

## 11. 更多命令

请参考[Job CLI](./cli/job.zh.md)和[Task CLI](./cli/task.zh.md)