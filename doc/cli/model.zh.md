## Model

### load

向 Fate-Serving 加载 `deploy` 生成的模型。

```bash
flow model load -c examples/model/publish_load_model.json
flow model load -j <job_id>
```

**选项**

| 参数      | 短格式 | 长格式        | 可选参数 | 说明     |
| --------- | ------ | ------------- | -------- | -------- |
| conf_path | `-c`   | `--conf-path` | 是       | 配置文件 |
| job_id    | `-j`   | `--job-id`    | 是       | 任务 ID  |

**样例**

```json
{
  "data": {
    "detail": {
      "guest": {
        "9999": {
          "retcode": 0,
          "retmsg": "success"
        }
      },
      "host": {
        "10000": {
          "retcode": 0,
          "retmsg": "success"
        }
      }
    },
    "guest": {
      "9999": 0
    },
    "host": {
      "10000": 0
    }
  },
  "jobId": "202111091122168817080",
  "retcode": 0,
  "retmsg": "success"
}
```

### bind

向 Fate-Serving 绑定 `deploy` 生成的模型。

```bash
flow model bind -c examples/model/bind_model_service.json
flow model bind -c examples/model/bind_model_service.json -j <job_id>
```

**选项**

| 参数      | 短格式 | 长格式        | 可选参数 | 说明     |
| --------- | ------ | ------------- | -------- | -------- |
| conf_path | `-c`   | `--conf-path` | 否       | 配置文件 |
| job_id    | `-j`   | `--job-id`    | 是       | 任务 ID  |

**样例**

```json
{
  "retcode": 0,
  "retmsg": "service id is 123"
}
```

### import

从本地或存储引擎中导入模型。

```bash
flow model import -c examples/model/import_model.json
flow model import -c examples/model/restore_model.json --from-database
```

**选项**

| 参数          | 短格式 | 长格式            | 可选参数 | 说明                 |
| ------------- | ------ | ----------------- | -------- | -------------------- |
| conf_path     | `-c`   | `--conf-path`     | 否       | 配置文件             |
| from_database |        | `--from-database` | 是       | 从存储引擎中导入模型 |

**样例**

```json
{
  "data": {
    "board_url": "http://127.0.0.1:8080/index.html#/dashboard?job_id=202111091125358161430&role=local&party_id=0",
    "code": 0,
    "dsl_path": "/root/Codes/FATE-Flow/jobs/202111091125358161430/job_dsl.json",
    "job_id": "202111091125358161430",
    "logs_directory": "/root/Codes/FATE-Flow/logs/202111091125358161430",
    "message": "success",
    "model_info": {
      "model_id": "local-0#model",
      "model_version": "202111091125358161430"
    },
    "pipeline_dsl_path": "/root/Codes/FATE-Flow/jobs/202111091125358161430/pipeline_dsl.json",
    "runtime_conf_on_party_path": "/root/Codes/FATE-Flow/jobs/202111091125358161430/local/0/job_runtime_on_party_conf.json",
    "runtime_conf_path": "/root/Codes/FATE-Flow/jobs/202111091125358161430/job_runtime_conf.json",
    "train_runtime_conf_path": "/root/Codes/FATE-Flow/jobs/202111091125358161430/train_runtime_conf.json"
  },
  "jobId": "202111091125358161430",
  "retcode": 0,
  "retmsg": "success"
}
```

### export

导出模型到本地或存储引擎中。

```bash
flow model export -c examples/model/export_model.json
flow model export -c examples/model/store_model.json --to-database
```

**选项**

| 参数        | 短格式 | 长格式          | 可选参数 | 说明                   |
| ----------- | ------ | --------------- | -------- | ---------------------- |
| conf_path   | `-c`   | `--conf-path`   | 否       | 配置文件               |
| to_database |        | `--to-database` | 是       | 将模型导出到存储引擎中 |

**样例**

```json
{
  "data": {
    "board_url": "http://127.0.0.1:8080/index.html#/dashboard?job_id=202111091124582110490&role=local&party_id=0",
    "code": 0,
    "dsl_path": "/root/Codes/FATE-Flow/jobs/202111091124582110490/job_dsl.json",
    "job_id": "202111091124582110490",
    "logs_directory": "/root/Codes/FATE-Flow/logs/202111091124582110490",
    "message": "success",
    "model_info": {
      "model_id": "local-0#model",
      "model_version": "202111091124582110490"
    },
    "pipeline_dsl_path": "/root/Codes/FATE-Flow/jobs/202111091124582110490/pipeline_dsl.json",
    "runtime_conf_on_party_path": "/root/Codes/FATE-Flow/jobs/202111091124582110490/local/0/job_runtime_on_party_conf.json",
    "runtime_conf_path": "/root/Codes/FATE-Flow/jobs/202111091124582110490/job_runtime_conf.json",
    "train_runtime_conf_path": "/root/Codes/FATE-Flow/jobs/202111091124582110490/train_runtime_conf.json"
  },
  "jobId": "202111091124582110490",
  "retcode": 0,
  "retmsg": "success"
}
```

### migrate

迁移模型。

```bash
flow model migrate -c examples/model/migrate_model.json
```

**选项**

| 参数      | 短格式 | 长格式        | 可选参数 | 说明     |
| --------- | ------ | ------------- | -------- | -------- |
| conf_path | `-c`   | `--conf-path` | 否       | 配置文件 |

**样例**

```json
{
  "data": {
    "arbiter": {
      "10000": 0
    },
    "detail": {
      "arbiter": {
        "10000": {
          "retcode": 0,
          "retmsg": "Migrating model successfully. The configuration of model has been modified automatically. New model id is: arbiter-100#guest-99#host-100#model, model version is: 202111091127392613050. Model files can be found at '/root/Codes/FATE-Flow/temp/fate_flow/arbiter#100#arbiter-100#guest-99#host-100#model_202111091127392613050.zip'."
        }
      },
      "guest": {
        "9999": {
          "retcode": 0,
          "retmsg": "Migrating model successfully. The configuration of model has been modified automatically. New model id is: arbiter-100#guest-99#host-100#model, model version is: 202111091127392613050. Model files can be found at '/root/Codes/FATE-Flow/temp/fate_flow/guest#99#arbiter-100#guest-99#host-100#model_202111091127392613050.zip'."
        }
      },
      "host": {
        "10000": {
          "retcode": 0,
          "retmsg": "Migrating model successfully. The configuration of model has been modified automatically. New model id is: arbiter-100#guest-99#host-100#model, model version is: 202111091127392613050. Model files can be found at '/root/Codes/FATE-Flow/temp/fate_flow/host#100#arbiter-100#guest-99#host-100#model_202111091127392613050.zip'."
        }
      }
    },
    "guest": {
      "9999": 0
    },
    "host": {
      "10000": 0
    }
  },
  "jobId": "202111091127392613050",
  "retcode": 0,
  "retmsg": "success"
}
```

### tag-list

获取模型的标签列表。

``` bash
flow model tag-list -j <job_id>
```

**选项**

| 参数   | 短格式 | 长格式     | 可选参数 | 说明    |
| ------ | ------ | ---------- | -------- | ------- |
| job_id | `-j`   | `--job_id` | 否       | 任务 ID |

### tag-model

从模型中添加或删除标签。

```bash
flow model tag-model -j <job_id> -t <tag_name>
flow model tag-model -j <job_id> -t <tag_name> --remove
```

**选项**

| 参数     | 短格式 | 长格式       | 可选参数 | 说明           |
| -------- | ------ | ------------ | -------- | -------------- |
| job_id   | `-j`   | `--job_id`   | 否       | 任务 ID        |
| tag_name | `-t`   | `--tag-name` | 否       | 标签名         |
| remove   |        | `--remove`   | 是       | 移除指定的标签 |

### deploy

配置预测 DSL。

```bash
flow model deploy --model-id <model_id> --model-version <model_version>
```

**选项**

| 参数           | 短格式 | 长格式             | 可选参数 | 说明                                                         |
| -------------- | ------ | ------------------ | -------- | ------------------------------------------------------------ |
| model_id       |        | `--model-id`       | 否       | 模型 ID                                                      |
| model_version  |        | `--model-version`  | 否       | 模型版本                                                     |
| cpn_list       |        | `--cpn-list`       | 是       | 组件列表                                                     |
| cpn_path       |        | `--cpn-path`       | 是       | 从文件中读入组件列表                                         |
| dsl_path       |        | `--dsl-path`       | 是       | 预测 DSL 文件                                                |
| cpn_step_index |        | `--cpn-step-index` | 是       | 用指定的 Checkpoint 模型替换 Pipeline 模型<br />使用 `:` 分隔 component name 与 step index<br />例如 `--cpn-step-index cpn_a:123` |
| cpn_step_name  |        | `--cpn-step-name`  | 是       | 用指定的 Checkpoint 模型替换 Pipeline 模型<br />使用 `:` 分隔 component name 与 step name<br />例如 `--cpn-step-name cpn_b:foobar` |

**样例**

```json
{
  "retcode": 0,
  "retmsg": "success",
  "data": {
    "model_id": "arbiter-9999#guest-10000#host-9999#model",
    "model_version": "202111032227378766180",
    "arbiter": {
      "party_id": 9999
    },
    "guest": {
      "party_id": 10000
    },
    "host": {
      "party_id": 9999
    },
    "detail": {
      "arbiter": {
        "party_id": {
          "retcode": 0,
          "retmsg": "deploy model of role arbiter 9999 success"
        }
      },
      "guest": {
        "party_id": {
          "retcode": 0,
          "retmsg": "deploy model of role guest 10000 success"
        }
      },
      "host": {
        "party_id": {
          "retcode": 0,
          "retmsg": "deploy model of role host 9999 success"
        }
      }
    }
  }
}
```

### get-predict-dsl

获取预测 DSL。

```bash
flow model get-predict-dsl --model-id <model_id> --model-version <model_version> -o ./examples/
```

**选项**

| 参数          | 短格式 | 长格式            | 可选参数 | 说明     |
| ------------- | ------ | ----------------- | -------- | -------- |
| model_id      |        | `--model-id`      | 否       | 模型 ID  |
| model_version |        | `--model-version` | 否       | 模型版本 |
| output_path   | `-o`   | `--output-path`   | 否       | 输出路径 |

### get-predict-conf

获取模型预测模板。

```bash
flow model get-predict-conf --model-id <model_id> --model-version <model_version> -o ./examples/
```

**选项**

| 参数          | 短格式 | 长格式            | 可选参数 | 说明     |
| ------------- | ------ | ----------------- | -------- | -------- |
| model_id      |        | `--model-id`      | 否       | 模型 ID  |
| model_version |        | `--model-version` | 否       | 模型版本 |
| output_path   | `-o`   | `--output-path`   | 否       | 输出路径 |

### get-model-info

获取模型信息。

```bash
flow model get-model-info --model-id <model_id> --model-version <model_version>
flow model get-model-info --model-id <model_id> --model-version <model_version> --detail
```

**选项**

| 参数          | 短格式 | 长格式            | 可选参数 | 说明         |
| ------------- | ------ | ----------------- | -------- | ------------ |
| model_id      |        | `--model-id`      | 否       | 模型 ID      |
| model_version |        | `--model-version` | 否       | 模型版本     |
| role          | `-r`   | `--role`          | 是       | Party 角色   |
| party_id      | `-p`   | `--party-id`      | 是       | Party ID     |
| detail        |        | `--detail`        | 是       | 展示详细信息 |

### homo-convert

基于横向训练的模型，生成其他 ML 框架的模型文件。

```bash
flow model homo-convert -c examples/model/homo_convert_model.json
```

**选项**

| 参数      | 短格式 | 长格式        | 可选参数 | 说明     |
| --------- | ------ | ------------- | -------- | -------- |
| conf_path | `-c`   | `--conf-path` | 否       | 配置文件 |

### homo-deploy

将横向训练后使用 `homo-convert` 生成的模型部署到在线推理系统中，当前支持创建基于 KFServing 的推理服务。

```bash
flow model homo-deploy -c examples/model/homo_deploy_model.json
```

**选项**

| 参数      | 短格式 | 长格式        | 可选参数 | 说明     |
| --------- | ------ | ------------- | -------- | -------- |
| conf_path | `-c`   | `--conf-path` | 否       | 配置文件 |
