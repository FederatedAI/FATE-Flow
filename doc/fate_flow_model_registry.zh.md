# FATE Flow 模型注册中心

[TOC]

## 1. 版本历史

| 版本状态 | 创建人 | 完成日期   | 备注   |
| -------- | ------ | ---------- | ------ |
| 1.0      | yuesun | 2021-11-04 | 初始化 |

## 2. 概述

每个组件运行完成后保存的模型称为 Pipeline 模型，在组件运行时定时保存的模型称为 Checkpoint 模型。Checkpoint 模型也可以用于组件运行意外中断后，重试时的“断点续传”。

Checkpoint 模型的支持自 1.7.0 加入，默认是不保存的，如需启用，则要向 DSL 中加入 callback `ModelCheckpoint`。

### 本地磁盘存储

- Pipeline 模型存储于 `model_local_cache/<party_model_id>/<model_version>/variables/data/<component_name>/<model_alias>`，
- Checkpoint 模型存储于 `model_local_cache/<party_model_id>/<model_version>/checkpoint/<component_name>/<step_index>#<step_name>`。

### 远端存储引擎

- 本地磁盘并不可靠，因此模型有丢失的风险，`FATE-Flow`支持导出模型到指定存储引擎、从指定存储引擎导入以及自动发布模型时推送模型到引擎存储
- 存储引擎支持腾讯云对象存储、MySQL 和 Redis, 具体请参考[存储引擎配置](#5-存储引擎配置)

## 3. Model

### `load`

**简要描述**

向 Fate-Serving 加载 `deploy` 生成的模型。

**请求参数**

| 参数      | 短格式 | 长格式        | 可选参数 | 说明     |
| --------- | ------ | ------------- | -------- | -------- |
| conf_path | `-c`   | `--conf-path` | 否       | 配置文件 |
| job_id    | `-j`   | `--job-id`    | 是       | 任务 ID  |

**请求CLI**

```bash
flow model load -c examples/model/publish_load_model.json
flow model load -c examples/model/publish_load_model.json -j <job_id>
```

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

### `bind`

**简要描述**

向 Fate-Serving 绑定 `deploy` 生成的模型。

**请求参数**

| 参数      | 短格式 | 长格式        | 可选参数 | 说明     |
| --------- | ------ | ------------- | -------- | -------- |
| conf_path | `-c`   | `--conf-path` | 否       | 配置文件 |
| job_id    | `-j`   | `--job-id`    | 是       | 任务 ID  |

**请求CLI**

```bash
flow model bind -c examples/model/bind_model_service.json
flow model bind -c examples/model/bind_model_service.json -j <job_id>
```

**样例**

```json
{
  "retcode": 0,
  "retmsg": "service id is 123"
}
```

### `import`

**简要描述**

从本地或存储引擎中导入模型。

**请求参数**

| 参数          | 短格式 | 长格式            | 可选参数 | 说明                             |
| ------------- | ------ | ----------------- | -------- | -------------------------------- |
| conf_path     | `-c`   | `--conf-path`     | 否       | 配置文件                         |
| from_database |        | `--from-database` | 是       | 从 Flow 配置的存储引擎中导入模型 |

**请求CLI**

```bash
flow model import -c examples/model/import_model.json
flow model import -c examples/model/restore_model.json --from-database
```

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

### `export`

**简要描述**

导出模型到本地或存储引擎中。

**请求参数**

| 参数        | 短格式 | 长格式          | 可选参数 | 说明                               |
| ----------- | ------ | --------------- | -------- | ---------------------------------- |
| conf_path   | `-c`   | `--conf-path`   | 否       | 配置文件                           |
| to_database |        | `--to-database` | 是       | 将模型导出到 Flow 配置的存储引擎中 |

**请求CLI**

```bash
flow model export -c examples/model/export_model.json
flow model export -c examplse/model/store_model.json --to-database
```

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

### `migrate`

**简要描述**

迁移模型。

**请求参数**

| 参数      | 短格式 | 长格式        | 可选参数 | 说明     |
| --------- | ------ | ------------- | -------- | -------- |
| conf_path | `-c`   | `--conf-path` | 否       | 配置文件 |

**请求CLI**

```bash
flow model migrate -c examples/model/migrate_model.json
```

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

### `tag-list`

**简要描述**

获取模型的标签列表。

**请求参数**

| 参数   | 短格式 | 长格式     | 可选参数 | 说明    |
| ------ | ------ | ---------- | -------- | ------- |
| job_id | `-j`   | `--job_id` | 否       | 任务 ID |

**请求CLI**

``` bash
flow model tag-list -j <job_id>
```

### `tag-model`

**简要描述**

向模型添加标签。

**请求参数**

| 参数     | 短格式 | 长格式       | 可选参数 | 说明           |
| -------- | ------ | ------------ | -------- | -------------- |
| job_id   | `-j`   | `--job_id`   | 否       | 任务 ID        |
| tag_name | `-t`   | `--tag-name` | 否       | 标签名         |
| remove   |        | `--remove`   | 是       | 移除指定的标签 |

**请求CLI**

```bash
flow model tag-model -j <job_id> -t <tag_name>
flow model tag-model -j <job_id> -t <tag_name> --remove
```

### `deploy`

**简要描述**

配置预测 DSL。

**请求参数**

| 参数           | 短格式 | 长格式             | 可选参数 | 说明                                                         |
| -------------- | ------ | ------------------ | -------- | ------------------------------------------------------------ |
| model_id       |        | `--model-id`       | 否       | 模型 ID                                                      |
| model_version  |        | `--model-version`  | 否       | 模型版本                                                     |
| cpn_list       |        | `--cpn-list`       | 是       | 组件列表                                                     |
| cpn_path       |        | `--cpn-path`       | 是       | 从文件中读入组件列表                                         |
| dsl_path       |        | `--dsl-path`       | 是       | 预测 DSL 文件                                                |
| cpn_step_index |        | `--cpn-step-index` | 是       | 用指定的 Checkpoint 模型替换 Pipeline 模型<br />使用 `:` 分隔 component name 与 step index<br />例如 `--cpn-step-index cpn_a:123` |
| cpn_step_name  |        | `--cpn-step-name`  | 是       | 用指定的 Checkpoint 模型替换 Pipeline 模型<br />使用 `:` 分隔 component name 与 step name<br />例如 `--cpn-step-name cpn_b:foobar` |

**请求CLI**

```bash
flow model deploy --model-id <model_id> --model-version <model_version>
```

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

### `get-predict-dsl`

**简要描述**

获取预测 DSL。

**请求参数**

| 参数          | 短格式 | 长格式            | 可选参数 | 说明     |
| ------------- | ------ | ----------------- | -------- | -------- |
| model_id      |        | `--model-id`      | 否       | 模型 ID  |
| model_version |        | `--model-version` | 否       | 模型版本 |
| output_path   | `-o`   | `--output-path`   | 否       | 输出路径 |

**请求CLI**

```bash
flow model get-predict-dsl --model-id <model_id> --model-version <model_version> -o ./examples/
```

### `get-predict-conf`

**简要描述**

模型预测模板。

**请求参数**

| 参数          | 短格式 | 长格式            | 可选参数 | 说明     |
| ------------- | ------ | ----------------- | -------- | -------- |
| model_id      |        | `--model-id`      | 否       | 模型 ID  |
| model_version |        | `--model-version` | 否       | 模型版本 |
| output_path   | `-o`   | `--output-path`   | 否       | 输出路径 |

**请求CLI**

```bash
flow model get-predict-conf --model-id <model_id> --model-version <model_version> -o ./examples/
```

### `get-model-info`

**简要描述**

获取模型信息。

**请求参数**

| 参数          | 短格式 | 长格式            | 可选参数 | 说明         |
| ------------- | ------ | ----------------- | -------- | ------------ |
| model_id      |        | `--model-id`      | 否       | 模型 ID      |
| model_version |        | `--model-version` | 否       | 模型版本     |
| role          | `-r`   | `--role`          | 是       | Party 角色   |
| party_id      | `-p`   | `--party-id`      | 是       | Party ID     |
| detail        |        | `--detail`        | 是       | 展示详细信息 |

**请求CLI**

```bash
flow model get-model-info --model-id <model_id> --model-version <model_version>
flow model get-model-info --model-id <model_id> --model-version <model_version> --detail
```

### `homo-convert`

**简要描述**

基于横向训练的模型，生成其他 ML  框架的模型文件。

**请求参数**

| 参数      | 短格式 | 长格式        | 可选参数 | 说明     |
| --------- | ------ | ------------- | -------- | -------- |
| conf_path | `-c`   | `--conf-path` | 否       | 配置文件 |

**请求CLI**

```bash
flow model homo-convert -c examples/model/homo_convert_model.json
```

### `homo-deploy`

**简要描述**

将横向训练后使用 `homo-convert` 生成的模型部署到在线推理系统中，当前支持创建基于 KFServing 的推理服务。

**请求参数**

| 参数      | 短格式 | 长格式        | 可选参数 | 说明             |
| --------- | ------ | ------------- | -------- | ---------------- |
| conf_path | `-c`   | `--conf-path` | 否       | 任务配置文件路径 |

**请求CLI**

```bash
flow model homo-deploy -c examples/model/homo_deploy_model.json
```

## 4. Checkpoint

### `list`

**简要描述**

获取 Checkpoint 模型列表。

**请求参数**

| 参数           | 短格式 | 长格式             | 可选参数 | 说明       |
| -------------- | ------ | ------------------ | -------- | ---------- |
| model_id       |        | `--model-id`       | 否       | 模型 ID    |
| model_version  |        | `--model-version`  | 否       | 模型版本   |
| role           | `-r`   | `--role`           | 否       | Party 角色 |
| party_id       | `-p`   | `--party-id`       | 否       | Party ID   |
| component_name | `-cpn` | `--component-name` | 否       | 组件名     |

**请求CLI**

```bash
flow checkpoint list --model-id <model_id> --model-version <model_version> --role <role> --party-id <party_id> --component-name <component_name>
```

**样例**

```json
{
  "retcode": 0,
  "retmsg": "success",
  "data": [
    {
      "create_time": "2021-11-07T02:34:54.683015",
      "step_index": 0,
      "step_name": "step_name",
      "models": {
        "HeteroLogisticRegressionMeta": {
          "buffer_name": "LRModelMeta",
          "sha1": "6871508f6e6228341b18031b3623f99a53a87147"
        },
        "HeteroLogisticRegressionParam": {
          "buffer_name": "LRModelParam",
          "sha1": "e3cb636fc93675684bff27117943f5bfa87f3029"
        }
      }
    }
  ]
}
```

### `get`

**简要描述**

获取 Checkpoint 模型信息。

**请求参数**

| 参数           | 短格式 | 长格式             | 可选参数 | 说明                                  |
| -------------- | ------ | ------------------ | -------- | ------------------------------------- |
| model_id       |        | `--model-id`       | 否       | 模型 ID                               |
| model_version  |        | `--model-version`  | 否       | 模型版本                              |
| role           | `-r`   | `--role`           | 否       | Party 角色                            |
| party_id       | `-p`   | `--party-id`       | 否       | Party ID                              |
| component_name | `-cpn` | `--component-name` | 否       | 组件名                                |
| step_index     |        | `--step-index`     | 是       | Step index，不可与 step_name 同时使用 |
| step_name      |        | `--step-name`      | 是       | Step name，不可与 step_index 同时使用 |

**请求CLI**

```bash
flow checkpoint get --model-id <model_id> --model-version <model_version> --role <role> --party-id <party_id> --component-name <component_name> --step-index <step_index>
```

**样例**

```json
{
  "retcode": 0,
  "retmsg": "success",
  "data": {
    "create_time": "2021-11-07T02:34:54.683015",
    "step_index": 0,
    "step_name": "step_name",
    "models": {
      "HeteroLogisticRegressionMeta": "CgJMMhEtQxzr4jYaPxkAAAAAAADwPyIHcm1zcHJvcDD///////////8BOTMzMzMzM8M/QApKBGRpZmZYAQ==",
      "HeteroLogisticRegressionParam": "Ig0KAng3EW1qASu+uuO/Ig0KAng0EcNi7a65ReG/Ig0KAng4EbJbl4gvVea/Ig0KAng2EcZwlVZTkOu/Ig0KAngwEVpG8dCbGvG/Ig0KAng5ESJNTx5MLve/Ig0KAngzEZ88H9P8qfO/Ig0KAng1EVfWP8JJv/K/Ig0KAngxEVS0xVXoTem/Ig0KAngyEaApgW32Q/K/KSiiE8AukPs/MgJ4MDICeDEyAngyMgJ4MzICeDQyAng1MgJ4NjICeDcyAng4MgJ4OUj///////////8B"
    }
  }
}
```

## 5. 存储引擎配置

### `enable_model_store`

开启后，在调用 `/model/load` 时：如果模型文件在本地磁盘存在、但不在存储引擎中，则自动把模型文件上传至存储引擎；如果模型文件在存储引擎存在、但不在本地磁盘中，则自动把模型文件下载到本地磁盘。

此配置不影响 `/model/store` 和 `/model/restore`。

### `model_store_address`

此配置定义使用的存储引擎。

#### 腾讯云对象存储

```yaml
storage: tencent_cos
# 请从腾讯云控制台获取下列配置
Region:
SecretId:
SecretKey:
Bucket:
```

#### MySQL

```yaml
storage: mysql
database: fate_model
user: fate
password: fate
host: 127.0.0.1
port: 3306
# 可选的数据库连接参数
max_connections: 10
stale_timeout: 10
```

#### Redis

```yaml
storage: redis
host: 127.0.0.1
port: 6379
db: 0
password:
# key 的超时时间，单位秒。默认 None，没有超时时间。
ex:
```
