# Multi-Party Job&Task Scheduling

## 1. Description

Mainly describes how to submit a federated learning job using `FATE Flow` and observe the use of

## 2. Job submission

- Build a federated learning job and submit it to the scheduling system for execution
- Two configuration files are required: job dsl and job conf
- job dsl configures the running components: list, input-output relationships
- job conf configures the component execution parameters, system operation parameters

{{snippet('cli/job.md', '### submit')}}

## 3. Job DSL configuration description

The configuration file of DSL is in json format, in fact, the whole configuration file is a json object (dict).

### 3.1 Component List

**Description** The first level of this dict is `components`, which indicates the modules that will be used by this job.
**Example**

```json
{
  "components" : {
          ...
      }
}
```

Each individual module is defined under "components", e.g.

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

All data needs to be fetched from the data store via the **Reader** module, note that this module only has the output `output`

```json
"reader_0": {
      "module": "Reader",
      "output": {
          "data": ["train"]
      }
}
```

### 3.2 Modules

**Description** Used to specify the components to be used, all optional module names refer to.
**Example**

```json
"hetero_feature_binning_1": {
    "module": "HeteroFeatureBinning",
     ...
}
```

### 3.3 Inputs

**Implications** Upstream inputs, divided into two input types, data and model.

#### data input

**Description** Upstream data input, divided into three input types.
    
    > 1. data: generally used in the data-transform module, feature_engineering module or
    > evaluation module.
    > 2. train_data: Generally used in homo_lr, hetero_lr and secure_boost
    > modules. If the train_data field is present, then the task will be recognized as a fit task
    > validate_data: If the train_data
    > field is present, then the field is optional. If you choose to keep this field, the data pointed to will be used as the
    > validation set
    > 4. test_data: Used as prediction data, if provided, along with model input.

#### model_input

**Description** Upstream model input, divided into two input types.
    1. model: Used for model input of the same type of component. For example, hetero_binning_0 will fit the model, and then
        hetero_binning_1 will use the output of hetero_binning_0 for predict or
        transform. code example.

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
                "data": ["validate_data" ],
              "model": ["eval_model"]
            }
        }
```
    2. isometric_model: Used to specify the model input of the inherited upstream component. For example, the upstream component of feature selection is
        feature binning, it will use the information of feature binning as the feature
        Code example.
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
                "data": [ "train" ],
                "model": ["output_model"]
            }
        }
```

### 3.4 Output

**Description** Output, like input, is divided into data and model output

#### data output

**Description** Data output, divided into four output types.

1. data: General module data output
2. train_data: only for Data Split
3. validate_data: Only for Data Split
4. test_data: Data Split only

#### Model Output

**Description** Model output, using model only

### 3.5 Component Providers

Since FATE-Flow version 1.7.0, the same FATE-Flow system supports loading multiple component providers, i.e. providers, which provide several components, and the source provider of the component can be configured when submitting a job

**Description** Specify the provider, support global specification and individual component specification; if not specified, the default provider: `fate@$FATE_VERSION`

**Format** `provider_name@$provider_version`

**Advanced** You can register a new provider through the component registration CLI, currently supported providers: fate and fate_sql, please refer to [FATE Flow Component Center](./fate_flow_component_registry.md)

**Example**

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

## 4. Job Conf Configuration Description

Job Conf is used to set the information of each participant, the parameters of the job and the parameters of each component. The contents include the following.

### 4.1 DSL Version

**Description** Configure the version, the default is not 1, it is recommended to configure 2
**Example**
```json
"dsl_version": "2"
```

### 4.2 Job participants

#### initiating party

**Description** The role and party_id of the assignment initiator.
**Example**
```json
"initiator": {
    "role": "guest",
    "party_id": 9999
}
```

#### All participants

**Description** Information about each participant.
**Description** In the role field, each element represents a role and the party_id that assumes that role. party_id for each role
    The party_id of each role is in the form of a list, since a task may involve multiple parties in the same role.
**Example**

```json
"role": {
    "guest": [9999],
    "host": [10000],
    "arbiter": [10000]
}
```

### 4.3 System operation parameters

**Description**
    Configure the main system parameters for job runtime

#### Parameter application scope policy setting

**Apply to all participants, use the common scope identifier
**Apply to only one participant, use the role scope identifier, use (role:)party_index to locate the specified participant, direct

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

The parameters under common are applied to all participants, and the parameters under role-guest-0 configuration are applied to the participants under the subscript 0 of the guest role.
Note that the current version of the system operation parameters are not strictly tested for application to only one participant, so it is recommended to use common as a preference.

#### Supported system parameters

| Configuration | Default | Supported | Description |
| ----------------------------- | --------------------- | ------------------------------- | ------------------------------------------------------------------------------------------------- |
| job_type | train | train, predict | task_cores |
| task_cores | 4 | positive_integer | total_cpu_cores_applied_to_job |
| task_parallelism | 1 | positive_integer | task_parallelism |
| computing_partitions | number of cpu cores allocated to task | positive integer | number of partitions in the data table at computation time |
| eggroll_run | none | processors_per_node, etc. | eggroll computing engine related configuration parameters, generally do not need to be configured, from task_cores automatically calculated, if configured, task_cores parameters do not take effect |
| spark_run | none | num-executors, executor-cores, etc. | spark compute engine related configuration parameters, generally do not need to be configured, automatically calculated by task_cores, if configured, task_cores parameters do not take effect |
| rabbitmq_run | None | queue, exchange, etc. | Configuration parameters for rabbitmq to create queue, exchange, etc., which are generally not required and take the system defaults.
| pulsar_run | none | producer, consumer, etc. | The configuration parameters for pulsar to create producer and consumer.                                        |
| federated_status_collect_type | PUSH | PUSH, PULL | Multi-party run status collection mode, PUSH means that each participant actively reports to the initiator, PULL means that the initiator periodically pulls from each participant.
| timeout | 259200 (3 days) | positive integer | task_timeout,unit_second |
| audo_retries | 3 | positive integer | maximum number of retries per task failure |
| model_id | \- | \- | The model id to be filled in for prediction tasks.
| model_version | \- | \- | Model version, required for prediction tasks

1. there is a certain support dependency between the computation engine and the storage engine
2. developers can implement their own adapted engines, and configure the engines in runtime config

#### reference configuration

1. no need to pay attention to the compute engine, take the system default cpu allocation compute policy when the configuration

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

2. use eggroll as the computing engine, take the configuration when specifying cpu and other parameters directly

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

3. use spark as the computing engine, rabbitmq as the federation engine, take the configuration when specifying the cpu and other parameters directly

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

4. use spark as the computing engine and pulsar as the federation engine

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
For more advanced resource-related configuration, please refer to [Resource Management](#4-Resource Management)

### 4.3 Component operation parameters

#### Parameter application scope policy setting

- Apply to all participants, use common scope identifier
- Apply to only one participant, use the role scope identifier, use (role:)party_index to locate the specified participant, directly specified parameters have higher priority than common parameters

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

where the parameters under the common configuration are applied to all participants, and the parameters under the role-guest-0 configuration indicate that they are applied to the participants under the subscript 0 of the guest role
Note that the current version of the component runtime parameter already supports two application scope policies

#### Reference Configuration

- For the `intersection_0` and `hetero_lr_0` components, the runtime parameters are placed under the common scope and are applied to all participants
- The operational parameters of `reader_0` and `data_transform_0` components are configured specific to each participant, because usually the input parameters are not consistent across participants, so usually these two components are set by participant
- The above component names are defined in the DSL configuration file

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

## 5. Multi-Host Configuration

Multi-Host task should list all host information under role

**Example**:

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

The different configurations for each host should be listed separately under their respective corresponding modules

**Example**:

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

## 6. Predictive Task Configuration

### 6.1 Description

DSL V2 does not automatically generate prediction dsl for the training task. Users need to deploy the modules in the required model using `Flow Client` first.
For detailed command description, please refer to [fate_flow_client](./fate_flow_client.md)

```bash
flow model deploy --model-id $model_id --model-version $model_version --cpn-list ...
```

Optionally, the user can add new modules to the prediction dsl, such as `Evaluation`

### 6.2 Sample

Training dsl.

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

Prediction dsl:

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

## 7. Job reruns

In `1.5.0`, we started to support re-running a job, but only failed jobs are supported.
Version `1.7.0` supports rerunning of successful jobs, and you can specify which component to rerun from, the specified component and its downstream components will be rerun, but other components will not be rerun

{{snippet('cli/job.md', '### rerun')}}

## 8. Job parameter update

In the actual production modeling process, it is necessary to constantly debug the component parameters and rerun, but not all components need to be adjusted and rerun at this time, so after `1.7.0` version support to modify a component parameter update, and with the `rerun` command on-demand rerun

{{snippet('cli/job.md', '### parameter-update')}}

## 9. Job scheduling policy

- Queuing by commit time
- Currently, only FIFO policy is supported, i.e. the scheduler will only scan the first job each time, if the first job is successful in requesting resources, it will start and get out of the queue, if the request fails, it will wait for the next round of scheduling.

## 10. dependency distribution

**Brief description:** 

- Support for distributing fate and python dependencies from client nodes;
- The work node does not need to deploy fate;
- Only fate on spark supports distribution mode in current version;

**Related parameters configuration**:

conf/service_conf.yaml:

```yaml
dependent_distribution: true
```

fate_flow/settings.py

```python
FATE_FLOW_UPDATE_CHECK = False
```

**Description:**

- dependent_distribution: dependent distribution switch;, off by default; when off, you need to deploy fate on each work node, and also fill in the configuration of spark in spark-env.sh to configure PYSPARK_DRIVER_PYTHON and PYSPARK_PYTHON.

- FATE_FLOW_UPDATE_CHECK: Dependency check switch, turned off by default; it will automatically check if the fate code has changed every time a task is submitted; if it has changed, the fate code dependency will be re-uploaded;

## 11. More commands

Please refer to [Job CLI](./cli/job.md) and [Task CLI](./cli/task.md)