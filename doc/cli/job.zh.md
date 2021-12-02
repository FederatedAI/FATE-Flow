## Job

### submit

通过两个配置文件：job dsl和job conf构建一个联邦学习作业，提交到调度系统执行

```bash
flow job submit [options]
```

**选项**

| 参数名          | 必选 | 类型   | 说明           |
| :-------------- | :--- | :----- | -------------- |
| -d, --dsl-path  | 是   | string | job dsl的路径  |
| -c, --conf-path | 是   | string | job conf的路径 |

**返回**

| 参数名                          | 类型   | 说明                                                                  |
| :------------------------------ | :----- | --------------------------------------------------------------------- |
| retcode                         | int    | 返回码                                                                |
| retmsg                          | string | 返回信息                                                              |
| jobId                           | string | 作业ID                                                                |
| data                            | dict   | 返回数据                                                              |
| data.dsl_path                   | string | 依据提交的dsl内容，由系统生成的实际运行dsl配置的存放路径              |
| data.runtime_conf_on_party_path | string | 依据提交的conf内容，由系统生成的在每个party实际运行conf配置的存放路径 |
| data.board_url                  | string | fateboard查看地址                                                     |
| data.model_info                 | dict   | 模型标识信息                                                          |

**样例** 

```json
{
    "data": {
        "board_url": "http://127.0.0.1:8080/index.html#/dashboard?job_id=202111061608424372620&role=guest&party_id=9999",
        "code": 0,
        "dsl_path": "$FATE_PROJECT_BASE/jobs/202111061608424372620/job_dsl.json",
        "job_id": "202111061608424372620",
        "logs_directory": "$FATE_PROJECT_BASE/logs/202111061608424372620",
        "message": "success",
        "model_info": {
            "model_id": "arbiter-10000#guest-9999#host-10000#model",
            "model_version": "202111061608424372620"
        },
        "pipeline_dsl_path": "$FATE_PROJECT_BASE/jobs/202111061608424372620/pipeline_dsl.json",
        "runtime_conf_on_party_path": "$FATE_FATE_PROJECT_BASE/jobs/202111061608424372620/guest/9999/job_runtime_on_party_conf.json",
        "runtime_conf_path": "$FATE_PROJECT_BASE/jobs/202111061608424372620/job_runtime_conf.json",
        "train_runtime_conf_path": "$FATE_PROJECT_BASE/jobs/202111061608424372620/train_runtime_conf.json"
    },
    "jobId": "202111061608424372620",
    "retcode": 0,
    "retmsg": "success"
}
```

### rerun

重新运行某个作业

```bash
flow job rerun [options]
```

**选项**

| 参数名                 | 必选 | 类型   | 说明                                                                                                  |
| :--------------------- | :--- | :----- | ----------------------------------------------------------------------------------------------------- |
| -j, --job-id           | 是   | string | job id 路径                                                                                           |
| -cpn, --component-name | 否   | string | 指定从哪个组件重跑，没被指定的组件若与指定组件没有上游依赖关系则不会执行;若不指定该参数则整个作业重跑 |
| --force                | 否   | bool   | 作业即使成功也重跑;若不指定该参数，作业如果成功，则跳过重跑                                           |

**返回**

| 参数名  | 类型   | 说明     |
| :------ | :----- | -------- |
| retcode | int    | 返回码   |
| retmsg  | string | 返回信息 |
| jobId   | string | 作业ID   |
| data    | dict   | 返回数据 |

**样例** 

```bash
flow job rerun -j 202111031100369723120
```

```bash
flow job rerun -j 202111031100369723120 -cpn hetero_lr_0
```

```bash
flow job rerun -j 202111031100369723120 -cpn hetero_lr_0 --force 
```

### parameter-update

更新作业参数

```bash
flow job parameter-update [options]
```

**选项**

| 参数名          | 必选 | 类型   | 说明                                                 |
| :-------------- | :--- | :----- | ---------------------------------------------------- |
| -j, --job-id    | 是   | string | job id 路径                                          |
| -c, --conf-path | 是   | string | 需要更新的job conf的内容，不需要更新的参数不需要填写 |

**返回**

| 参数名  | 类型   | 说明                 |
| :------ | :----- | -------------------- |
| retcode | int    | 返回码               |
| retmsg  | string | 返回信息             |
| jobId   | string | 作业ID               |
| data    | dict   | 返回更新后的job conf |

**样例** 

假设更新job中hetero_lr_0这个组件的部分执行参数，配置文件如下：
```bash
{
  "job_parameters": {
  },
  "component_parameters": {
    "common": {
      "hetero_lr_0": {
        "alpha": 0.02,
        "max_iter": 5
      }
    }
  }
}
```

执行如下命令生效：

```bash
flow job parameter-update -j 202111061957421943730 -c examples/other/update_parameters.json
```

执行如下命令重跑：

```bash
flow job rerun -j 202111061957421943730 -cpn hetero_lr_0 --force 
```

### stop

取消或终止指定任务

**选项**

| 编号 | 参数   | 短格式 | 长格式     | 必要参数 | 参数介绍 |
| ---- | ------ | ------ | ---------- | -------- | -------- |
| 1    | job_id | `-j`   | `--job_id` | 是       | Job ID   |

**样例**

``` bash
flow job stop -j $JOB_ID
```

### query

检索任务信息。
**选项**

| 编号 | 参数     | 短格式 | 长格式       | 必要参数 | 参数介绍 |
| ---- | -------- | ------ | ------------ | -------- | -------- |
| 1    | job_id   | `-j`   | `--job_id`   | 否       | Job ID   |
| 2    | role     | `-r`   | `--role`     | 否       | 角色     |
| 3    | party_id | `-p`   | `--party_id` | 否       | Party ID |
| 4    | status   | `-s`   | `--status`   | 否       | 任务状态 |

**样例**：

``` bash
flow job query -r guest -p 9999 -s complete
flow job query -j $JOB_ID
```

### view

检索任务数据视图。
**选项**

| 编号 | 参数     | 短格式 | 长格式       | 必要参数 | 参数介绍 |
| ---- | -------- | ------ | ------------ | -------- | -------- |
| 1    | job_id   | `-j`   | `--job_id`   | 是       | Job ID   |
| 2    | role     | `-r`   | `--role`     | 否       | 角色     |
| 3    | party_id | `-p`   | `--party_id` | 否       | Party ID |
| 4    | status   | `-s`   | `--status`   | 否       | 任务状态 |

**样例**：

``` bash
flow job view -j $JOB_ID -s complete
```

### config

下载指定任务的配置文件到指定目录。
**选项**

| 编号 | 参数        | 短格式 | 长格式          | 必要参数 | 参数介绍 |
| ---- | ----------- | ------ | --------------- | -------- | -------- |
| 1    | job_id      | `-j`   | `--job_id`      | 是       | Job ID   |
| 2    | role        | `-r`   | `--role`        | 是       | 角色     |
| 3    | party_id    | `-p`   | `--party_id`    | 是       | Party ID |
| 4    | output_path | `-o`   | `--output-path` | 是       | 输出目录 |

**样例**：

``` bash
flow job config -j $JOB_ID -r host -p 10000 --output-path ./examples/
```

### log

下载指定任务的日志文件到指定目录。
**选项**

| 编号 | 参数        | 短格式 | 长格式          | 必要参数 | 参数介绍 |
| ---- | ----------- | ------ | --------------- | -------- | -------- |
| 1    | job_id      | `-j`   | `--job_id`      | 是       | Job ID   |
| 2    | output_path | `-o`   | `--output-path` | 是       | 输出目录 |

**样例**：

``` bash
flow job log -j JOB_ID --output-path ./examples/
```

### list

展示任务列表。
**选项**

| 编号 | 参数  | 短格式 | 长格式    | 必要参数 | 参数介绍                 |
| ---- | ----- | ------ | --------- | -------- | ------------------------ |
| 1    | limit | `-l`   | `--limit` | 否       | 返回数量限制（默认：10） |

**样例**：

``` bash
flow job list
flow job list -l 30
```

### dsl

预测DSL文件生成器。
**选项**

| 编号 | 参数           | 短格式 | 长格式             | 必要参数 | 参数介绍                         |
| ---- | -------------- | ------ | ------------------ | -------- | -------------------------------- |
| 1    | cpn_list       |        | `--cpn-list`       | 否       | 用户指定组件名列表               |
| 2    | cpn_path       |        | `--cpn-path`       | 否       | 用户指定带有组件名列表的文件路径 |
| 3    | train_dsl_path |        | `--train-dsl-path` | 是       | 训练dsl文件路径                  |
| 4    | output_path    | `-o`   | `--output-path`    | 否       | 输出目录路径                     |

**样例**：

``` bash
flow job dsl --cpn-path fate_flow/examples/component_list.txt --train-dsl-path fate_flow/examples/test_hetero_lr_job_dsl.json

flow job dsl --cpn-path fate_flow/examples/component_list.txt --train-dsl-path fate_flow/examples/test_hetero_lr_job_dsl.json -o fate_flow/examples/

flow job dsl --cpn-list "dataio_0, hetero_feature_binning_0, hetero_feature_selection_0, evaluation_0" --train-dsl-path fate_flow/examples/test_hetero_lr_job_dsl.json -o fate_flow/examples/

flow job dsl --cpn-list [dataio_0,hetero_feature_binning_0,hetero_feature_selection_0,evaluation_0] --train-dsl-path fate_flow/examples/test_hetero_lr_job_dsl.json -o fate_flow/examples/
```
