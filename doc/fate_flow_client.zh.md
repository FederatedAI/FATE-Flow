# FATE Flow 客户端

[TOC]

## 1. 说明

- 介绍如何安装使用`FATE Flow Client`，其通常包含在`FATE Client`中，`FATE Client`包含了`FATE项目`多个客户端：`Pipeline` `FATE Flow Client` `FATE Test`
- 介绍`FATE Flow Client`提供的命令行，所有的命令将有一个共有调用入口，您可以在命令行中键入`flow`以获取所有的命令分类及其子命令。

```bash
    [IN]
    flow

    [OUT]
    Usage： flow [OPTIONS] COMMAND [ARGS]...

      Fate Flow Client

    Options：
      -h, --help  Show this message and exit.

    Commands：
      component   Component Operations
      data        Data Operations
      init        Flow CLI Init Command
      job         Job Operations
      model       Model Operations
      queue       Queue Operations
      table       Table Operations
      task        Task Operations
```

更多信息，请查阅如下文档或使用`flow --help`命令。

## 2. 安装FATE Client

### 2.1 在线安装

FATE Client会发布到`pypi`，可直接使用`pip`等工具安装对应版本，如

```bash
pip install fate-client
```

或者

```bash
pip install fate-client==${version}
```

### 2.2 在FATE集群上安装

请在装有1.5.1及其以上版本fate的机器中进行安装：

安装命令：

```shell
cd $FATE_PROJECT_BASE/
# 进入FATE PYTHON的虚拟环境
source bin/init_env.sh
# 执行安装
cd ./fate/python/fate_client && python setup.py install
```

安装完成之后，在命令行键入`flow` 并回车，获得如下返回即视为安装成功：

```shell
Usage: flow [OPTIONS] COMMAND [ARGS]...

  Fate Flow Client

Options:
  -h, --help  Show this message and exit.

Commands:
  component  Component Operations
  data       Data Operations
  init       Flow CLI Init Command
  job        Job Operations
  model      Model Operations
  queue      Queue Operations
  table      Table Operations
  tag        Tag Operations
  task       Task Operations
```

## 3. 初始化

在使用fate-client之前需要对其进行初始化，推荐使用fate的配置文件进行初始化，初始化命令如下：

### 3.1 指定fateflow服务地址

```bash
# 指定fateflow的IP地址和端口进行初始化
flow init --ip 192.168.0.1 --port 9380
```

### 3.2 通过FATE集群上的配置文件

```shell
# 进入FATE的安装路径，例如/data/projects/fate
cd $FATE_PROJECT_BASE/
flow init -c ./conf/service_conf.yaml
```

获得如下返回视为初始化成功：

```json
{
    "retcode": 0,
    "retmsg": "Fate Flow CLI has been initialized successfully."
}
```

## 4. 验证

主要验证客户端是否能连接上`FATE Flow Server`，如尝试查询当前的作业情况

```bash
flow job query
```

一般返回中的`retcode`为`0`即可

```json
{
    "data": [],
    "retcode": 0,
    "retmsg": "no job could be found"
}
```

如返回类似如下，则表明连接不上，请检查网络情况

```json
{
    "retcode": 100,
    "retmsg": "Connection refused. Please check if the fate flow service is started"
}
```

## 5.1 Data

### `upload`

**简要描述：** 

- 用于上传建模任务的输入数据到fate所支持的存储系统

**请求CLI** 

- `flow data upload -c $conf_path`

注: conf_path为参数路径，具体参数如下

**请求参数** 

| 参数名              | 必选 | 类型         | 说明                                                         |
| :------------------ | :--- | :----------- | ------------------------------------------------------------ |
| file                | 是   | string       | 数据存储路径                                                 |
| id_delimiter        | 是   | string       | 数据分隔符,如","                                             |
| head                | 否   | int          | 数据是否有表头                                               |
| partition           | 是   | int          | 数据分区数                                                   |
| storage_engine      | 否   | 存储引擎类型 | 默认"EGGROLL"，还支持"HDFS","LOCALFS", "HIVE"等              |
| namespace           | 是   | string       | 表命名空间                                                   |
| table_name          | 是   | string       | 表名                                                         |
| storage_address     | 否   | object       | 需要填写对应存储引擎的存储地址                               |
| use_local_data      | 否   | int          | 默认1，代表使用client机器的数据;0代表使用fate flow服务所在机器的数据 |
| drop                | 否   | int          | 是否覆盖上传                                                 |
| extend_sid          | 否   | bool         | 是否新增一列uuid id，默认False                               |
| auto_increasing_sid | 否   | bool         | 新增的id列是否自增(extend_sid为True才会生效), 默认False      |

**样例** 

- eggroll

  ```json
  {
      "file": "examples/data/breast_hetero_guest.csv",
      "id_delimiter": ",",
      "head": 1,
      "partition": 10,
      "namespace": "experiment",
      "table_name": "breast_hetero_guest",
      "storage_engine": "EGGROLL"
  }
  ```

- hdfs

  ```json
  {
      "file": "examples/data/breast_hetero_guest.csv",
      "id_delimiter": ",",
      "head": 1,
      "partition": 10,
      "namespace": "experiment",
      "table_name": "breast_hetero_guest",
      "storage_engine": "HDFS"
  }
  ```

- localfs

  ```json
  {
      "file": "examples/data/breast_hetero_guest.csv",
      "id_delimiter": ",",
      "head": 1,
      "partition": 4,
      "namespace": "experiment",
      "table_name": "breast_hetero_guest",
      "storage_engine": "LOCALFS"
  }
  ```

**返回参数** 

| 参数名  | 类型   | 说明     |
| :------ | :----- | -------- |
| jobId   | string | 任务id   |
| retcode | int    | 返回码   |
| retmsg  | string | 返回信息 |
| data    | object | 返回数据 |

**样例** 

```shell
{
    "data": {
        "board_url": "http://xxx.xxx.xxx.xxx:8080/index.html#/dashboard?job_id=202111081218319075660&role=local&party_id=0",
        "code": 0,
        "dsl_path": "/data/projects/fate/jobs/202111081218319075660/job_dsl.json",
        "job_id": "202111081218319075660",
        "logs_directory": "/data/projects/fate/logs/202111081218319075660",
        "message": "success",
        "model_info": {
            "model_id": "local-0#model",
            "model_version": "202111081218319075660"
        },
        "namespace": "experiment",
        "pipeline_dsl_path": "/data/projects/fate/jobs/202111081218319075660/pipeline_dsl.json",
        "runtime_conf_on_party_path": "/data/projects/fate/jobs/202111081218319075660/local/0/job_runtime_on_party_conf.json",
        "runtime_conf_path": "/data/projects/fate/jobs/202111081218319075660/job_runtime_conf.json",
        "table_name": "breast_hetero_host",
        "train_runtime_conf_path": "/data/projects/fate/jobs/202111081218319075660/train_runtime_conf.json"
    },
    "jobId": "202111081218319075660",
    "retcode": 0,
    "retmsg": "success"
}

```

### `download`
**简要描述：** 

- 用于下载fate存储引擎内的数据到文件格式数据

**请求CLI** 

- `flow data download -c $conf_path`

注: conf_path为参数路径，具体参数如下

**请求参数** 

| 参数名      | 必选 | 类型   | 说明           |
| :---------- | :--- | :----- | -------------- |
| output_path | 是   | string | 下载路径       |
| table_name  | 是   | string | fate表名       |
| namespace   | 是   | int    | fate表命名空间 |

样例:

```json
{
  "output_path": "/data/projects/fate/breast_hetero_guest.csv",
  "namespace": "experiment",
  "table_name": "breast_hetero_guest"
}
```

**返回参数** 

| 参数名  | 类型   | 说明     |
| :------ | :----- | -------- |
| retcode | int    | 返回码   |
| retmsg  | string | 返回信息 |
| data    | object | 返回数据 |

样例

```json
{
    "data": {
        "board_url": "http://xxx.xxx.xxx.xxx:8080/index.html#/dashboard?job_id=202111081457135282090&role=local&party_id=0",
        "code": 0,
        "dsl_path": "/data/projects/fate/jobs/202111081457135282090/job_dsl.json",
        "job_id": "202111081457135282090",
        "logs_directory": "/data/projects/fate/logs/202111081457135282090",
        "message": "success",
        "model_info": {
            "model_id": "local-0#model",
            "model_version": "202111081457135282090"
        },
        "pipeline_dsl_path": "/data/projects/fate/jobs/202111081457135282090/pipeline_dsl.json",
        "runtime_conf_on_party_path": "/data/projects/fate/jobs/202111081457135282090/local/0/job_runtime_on_party_conf.json",
        "runtime_conf_path": "/data/projects/fate/jobs/202111081457135282090/job_runtime_conf.json",
        "train_runtime_conf_path": "/data/projects/fate/jobs/202111081457135282090/train_runtime_conf.json"
    },
    "jobId": "202111081457135282090",
    "retcode": 0,
    "retmsg": "success"
}

```

## 6. Job

### `submit`

-   *介绍*： 提交执行pipeline任务。
-   *参数*：

| 编号 | 参数      | Flag_1 | Flag_2        | 必要参数 | 参数介绍                                                                                                   |
| ---- | --------- | ------ | ------------- | -------- | ---------------------------------------------------------------------------------------------------------- |
| 1    | conf_path | `-c`   | `--conf-path` | 是       | 任务配置文件路径                                                                                           |
| 2    | dsl_path  | `-d`   | `--dsl-path`  | 否       | DSL文件路径. 如果任务为预测任务，该字段可以不输入。另外，用户可以提供可用的自定义DSL文件用于执行预测任务。 |

-   *示例*：

``` bash
flow job submit -c fate_flow/examples/test_hetero_lr_job_conf.json -d fate_flow/examples/test_hetero_lr_job_dsl.json
```

### `stop`

-   *介绍*： 取消或终止指定任务。
-   *参数*：

| 编号 | 参数   | Flag_1 | Flag_2     | 必要参数 | 参数介绍 |
| ---- | ------ | ------ | ---------- | -------- | -------- |
| 1    | job_id | `-j`   | `--job_id` | 是       | Job ID   |

-   *示例*：

    ``` bash
    flow job stop -j $JOB_ID
    ```

### `query`

-   *介绍*： 检索任务信息。
-   *参数*：

| 编号 | 参数     | Flag_1 | Flag_2       | 必要参数 | 参数介绍 |
| ---- | -------- | ------ | ------------ | -------- | -------- |
| 1    | job_id   | `-j`   | `--job_id`   | 否       | Job ID   |
| 2    | role     | `-r`   | `--role`     | 否       | 角色     |
| 3    | party_id | `-p`   | `--party_id` | 否       | Party ID |
| 4    | status   | `-s`   | `--status`   | 否       | 任务状态 |

-   *示例*：

    ``` bash
    flow job query -r guest -p 9999 -s complete
    flow job query -j $JOB_ID
    ```

### `view`

-   *介绍*： 检索任务数据视图。
-   *参数*：

| 编号 | 参数     | Flag_1 | Flag_2       | 必要参数 | 参数介绍 |
| ---- | -------- | ------ | ------------ | -------- | -------- |
| 1    | job_id   | `-j`   | `--job_id`   | 是       | Job ID   |
| 2    | role     | `-r`   | `--role`     | 否       | 角色     |
| 3    | party_id | `-p`   | `--party_id` | 否       | Party ID |
| 4    | status   | `-s`   | `--status`   | 否       | 任务状态 |

-   *示例*：

    ``` bash
    flow job view -j $JOB_ID -s complete
    ```

### `config`

-   *介绍*： 下载指定任务的配置文件到指定目录。
-   *参数*：

| 编号 | 参数        | Flag_1 | Flag_2          | 必要参数 | 参数介绍 |
| ---- | ----------- | ------ | --------------- | -------- | -------- |
| 1    | job_id      | `-j`   | `--job_id`      | 是       | Job ID   |
| 2    | role        | `-r`   | `--role`        | 是       | 角色     |
| 3    | party_id    | `-p`   | `--party_id`    | 是       | Party ID |
| 4    | output_path | `-o`   | `--output-path` | 是       | 输出目录 |

-   *示例*：

    ``` bash
    flow job config -j $JOB_ID -r host -p 10000 --output-path ./examples/
    ```

### `log`

-   *介绍*： 下载指定任务的日志文件到指定目录。
-   *参数*：

| 编号 | 参数        | Flag_1 | Flag_2          | 必要参数 | 参数介绍 |
| ---- | ----------- | ------ | --------------- | -------- | -------- |
| 1    | job_id      | `-j`   | `--job_id`      | 是       | Job ID   |
| 2    | output_path | `-o`   | `--output-path` | 是       | 输出目录 |

-   *示例*：

    ``` bash
    flow job log -j JOB_ID --output-path ./examples/
    ```

### `list`

-   *介绍*： 展示任务列表。
-   *参数*：

| 编号 | 参数  | Flag_1 | Flag_2    | 必要参数 | 参数介绍                 |
| ---- | ----- | ------ | --------- | -------- | ------------------------ |
| 1    | limit | `-l`   | `--limit` | 否       | 返回数量限制（默认：10） |

-   *示例*：

``` bash
flow job list
flow job list -l 30
```

### `dsl`

-   *介绍*： 预测DSL文件生成器。
-   *参数*：

| 编号 | 参数           | Flag_1 | Flag_2             | 必要参数 | 参数介绍                         |
| ---- | -------------- | ------ | ------------------ | -------- | -------------------------------- |
| 1    | cpn_list       |        | `--cpn-list`       | 否       | 用户指定组件名列表               |
| 2    | cpn_path       |        | `--cpn-path`       | 否       | 用户指定带有组件名列表的文件路径 |
| 3    | train_dsl_path |        | `--train-dsl-path` | 是       | 训练dsl文件路径                  |
| 4    | output_path    | `-o`   | `--output-path`    | 否       | 输出目录路径                     |

-   *示例*：

``` bash
flow job dsl --cpn-path fate_flow/examples/component_list.txt --train-dsl-path fate_flow/examples/test_hetero_lr_job_dsl.json

flow job dsl --cpn-path fate_flow/examples/component_list.txt --train-dsl-path fate_flow/examples/test_hetero_lr_job_dsl.json -o fate_flow/examples/

flow job dsl --cpn-list "dataio_0, hetero_feature_binning_0, hetero_feature_selection_0, evaluation_0" --train-dsl-path fate_flow/examples/test_hetero_lr_job_dsl.json -o fate_flow/examples/

flow job dsl --cpn-list [dataio_0,hetero_feature_binning_0,hetero_feature_selection_0,evaluation_0] --train-dsl-path fate_flow/examples/test_hetero_lr_job_dsl.json -o fate_flow/examples/
```

## 7. Tracking

### `parameters`

-   *介绍*： 检索指定组件的参数。
-   *参数*：

| 编号 | 参数           | Flag_1 | Flag_2             | 必要参数 | 参数介绍 |
| ---- | -------------- | ------ | ------------------ | -------- | -------- |
| 1    | job_id         | `-j`   | `--job_id`         | 是       | Job ID   |
| 2    | role           | `-r`   | `--role`           | 是       | 角色     |
| 3    | party_id       | `-p`   | `--party_id`       | 是       | Party ID |
| 4    | component_name | `-cpn` | `--component_name` | 是       | 组件名   |

-   *示例*：

``` bash
flow component parameters -j $JOB_ID -r host -p 10000 -cpn hetero_feature_binning_0
```

### `metric-all`

-   *介绍*： 检索指定任务的所有metric数据。
-   *参数*：

| 编号 | 参数           | Flag_1 | Flag_2             | 必要参数 | 参数介绍 |
| ---- | -------------- | ------ | ------------------ | -------- | -------- |
| 1    | job_id         | `-j`   | `--job_id`         | 是       | Job ID   |
| 2    | role           | `-r`   | `--role`           | 是       | 角色     |
| 3    | party_id       | `-p`   | `--party_id`       | 是       | Party ID |
| 4    | component_name | `-cpn` | `--component_name` | 是       | 组件名   |

-   *示例*：

    ``` bash
    flow component metric-all -j $JOB_ID -r host -p 10000 -cpn hetero_feature_binning_0
    ```

### `metrics`

-   *介绍*： 检索指定任务指定组件的metric数据。
-   *参数*：

| 编号 | 参数           | Flag_1 | Flag_2             | 必要参数 | 参数介绍 |
| ---- | -------------- | ------ | ------------------ | -------- | -------- |
| 1    | job_id         | `-j`   | `--job_id`         | 是       | Job ID   |
| 2    | role           | `-r`   | `--role`           | 是       | 角色     |
| 3    | party_id       | `-p`   | `--party_id`       | 是       | Party ID |
| 4    | component_name | `-cpn` | `--component_name` | 是       | 组件名   |

-   *示例*：

    ``` bash
    flow component metrics -j $JOB_ID -r host -p 10000 -cpn hetero_feature_binning_0
    ```

### `metric-delete`

-   *介绍*： 删除指定metric数据。
-   *参数*：

| 编号 | 参数   | Flag_1 | Flag_2     | 必要参数 | 参数介绍                 |
| ---- | ------ | ------ | ---------- | -------- | ------------------------ |
| 1    | date   | `-d`   | `--date`   | 否       | 8位日期, 形如 'YYYYMMDD' |
| 2    | job_id | `-j`   | `--job_id` | 否       | Job ID                   |

-   *示例*：

``` bash
# 注意：如果同时键入date参数与job_id参数，CLI将优先检测date参数数据，job_id参数将被忽略。
flow component metric-delete -d 20200101
flow component metric-delete -j $JOB_ID
```

### `output-model`

-   *介绍*： 检索指定组件模型。
-   *参数*：

| 编号 | 参数           | Flag_1 | Flag_2             | 必要参数 | 参数介绍 |
| ---- | -------------- | ------ | ------------------ | -------- | -------- |
| 1    | job_id         | `-j`   | `--job_id`         | 是       | Job ID   |
| 2    | role           | `-r`   | `--role`           | 是       | 角色     |
| 3    | party_id       | `-p`   | `--party_id`       | 是       | Party ID |
| 4    | component_name | `-cpn` | `--component_name` | 是       | 组件名   |

-   *示例*：

    ``` bash
    flow component output-model -j $JOB_ID -r host -p 10000 -cpn hetero_feature_binning_0
    ```

### `output-data`

-   *介绍*： 下载指定组件的输出数据。
-   *参数*：

| 编号 | 参数           | Flag_1 | Flag_2             | 必要参数 | 参数介绍     |
| ---- | -------------- | ------ | ------------------ | -------- | ------------ |
| 1    | job_id         | `-j`   | `--job_id`         | 是       | Job ID       |
| 2    | role           | `-r`   | `--role`           | 是       | 角色         |
| 3    | party_id       | `-p`   | `--party_id`       | 是       | Party ID     |
| 4    | component_name | `-cpn` | `--component_name` | 是       | 组件名       |
| 5    | output_path    | `-o`   | `--output-path`    | 是       | 输出目录     |
| 6    | limit          | `-l`   | `--limit`          | 否       | 默认返回全部 |

-   *示例*：

    ``` bash
    flow component output-data -j $JOB_ID -r host -p 10000 -cpn hetero_feature_binning_0 --output-path ./examples/
    ```

### `output-data-table`

-   *介绍*： 查看数据表名及命名空间。
-   *参数*：

| 编号 | 参数           | Flag_1 | Flag_2             | 必要参数 | 参数介绍 |
| ---- | -------------- | ------ | ------------------ | -------- | -------- |
| 1    | job_id         | `-j`   | `--job_id`         | 是       | Job ID   |
| 2    | role           | `-r`   | `--role`           | 是       | 角色     |
| 3    | party_id       | `-p`   | `--party_id`       | 是       | Party ID |
| 4    | component_name | `-cpn` | `--component_name` | 是       | 组件名   |

-   *示例*：

    ``` bash
    flow component output-data-table -j $JOB_ID -r host -p 10000 -cpn hetero_feature_binning_0
    ```

### `list`

-   *介绍*： 展示指定任务的组件列表。
-   *参数*：

| 编号 | 参数   | Flag_1 | Flag_2     | 必要参数 | 参数介绍 |
| ---- | ------ | ------ | ---------- | -------- | -------- |
| 1    | job_id | `-j`   | `--job_id` | 是       | Job ID   |

-   *示例*：

``` bash
flow component list -j $JOB_ID
```

### `get-summary`

-   *介绍*： 获取指定组件的概要。
-   *参数*：

| 编号 | 参数           | Flag_1 | Flag_2             | 必要参数 | 参数介绍     |
| ---- | -------------- | ------ | ------------------ | -------- | ------------ |
| 1    | job_id         | `-j`   | `--job_id`         | 是       | Job ID       |
| 2    | role           | `-r`   | `--role`           | 是       | 角色         |
| 3    | party_id       | `-p`   | `--party_id`       | 是       | Party ID     |
| 4    | component_name | `-cpn` | `--component_name` | 是       | 组件名       |
| 5    | output_path    | `-o`   | `--output-path`    | 否       | 输出目录路径 |

-   *示例*：

``` bash
flow component get-summary -j $JOB_ID -r host -p 10000 -cpn hetero_feature_binning_0

flow component get-summary -j $JOB_ID -r host -p 10000 -cpn hetero_feature_binning_0 -o ./examples/
```

## 8. Model

### `load`

-   *介绍*： 加载模型。
-   *参数*：

| 编号 | 参数      | Flag_1 | Flag_2        | 必要参数 | 参数介绍         |
| ---- | --------- | ------ | ------------- | -------- | ---------------- |
| 1    | conf_path | `-c`   | `--conf-path` | 否       | 任务配置文件路径 |
| 2    | job_id    | `-j`   | `--job_id`    | 否       | Job ID           |

-   *示例*：

``` bash
flow model load -c fate_flow/examples/publish_load_model.json
flow model load -j $JOB_ID
```

### `bind`

-   *介绍*： 绑定模型。如果 <span class="title-ref">dsl_version</span>
    == <span class="title-ref">2</span> 则需要先部署（\`deploy\`）模型。
-   *参数*：

| 编号 | 参数      | Flag_1 | Flag_2        | 必要参数 | 参数介绍         |
| ---- | --------- | ------ | ------------- | -------- | ---------------- |
| 1    | conf_path | `-c`   | `--conf-path` | 是       | 任务配置文件路径 |
| 2    | job_id    | `-j`   | `--job_id`    | 否       | Job ID           |

-   *示例*：

``` bash
flow model bind -c fate_flow/examples/bind_model_service.json
flow model bind -c fate_flow/examples/bind_model_service.json -j $JOB_ID
```

### `import`

-   *介绍*： 导入模型。如果 <span class="title-ref">dsl_version</span>
    == <span class="title-ref">2</span> 则需要先部署（\`deploy\`）模型。
-   *参数*：

| 编号 | 参数          | Flag_1 | Flag_2          | 必要参数 | 参数介绍                                                                        |
| ---- | ------------- | ------ | --------------- | -------- | ------------------------------------------------------------------------------- |
| 1    | conf_path     | `-c`   | `--conf-path`   | 是       | 任务配置文件路径                                                                |
| 2    | from-database |        | --from-database | 否       | 如果指定且有可用的数据库环境，fate flow将从根据任务配置文件从数据库中导入模型。 |

-   *示例*：

``` bash
flow model import -c fate_flow/examples/import_model.json
flow model import -c fate_flow/examples/restore_model.json --from-database
```

### `export`

-   *介绍*： 导出模型。
-   *参数*：

| 编号 | 参数        | Flag_1 | Flag_2          | 必要参数 | 参数介绍                                                                          |
| ---- | ----------- | ------ | --------------- | -------- | --------------------------------------------------------------------------------- |
| 1    | conf_path   | `-c`   | `--conf-path`   | 是       | 任务配置文件路径                                                                  |
| 2    | to-database |        | `--to-database` | 否       | 如果指定且有可用的数据库环境，fate flow将从根据任务配置文件将模型导出到数据库中。 |

-   *示例*：

``` bash
flow model export -c fate_flow/examples/export_model.json
flow model export -c fate_flow/examplse/store_model.json --to-database
```

### `migrate`

-   *介绍*： 迁移模型。
-   *参数*：

| 编号 | 参数      | Flag_1 | Flag_2        | 必要参数 | 参数介绍         |
| ---- | --------- | ------ | ------------- | -------- | ---------------- |
| 1    | conf_path | `-c`   | `--conf-path` | 是       | 任务配置文件路径 |

-   *示例*：

``` bash
flow model migrate -c fate_flow/examples/migrate_model.json
```

### `tag-list`

-   *介绍*： 展示模型的标签列表。
-   *参数*：

| 编号 | 参数   | Flag_1 | Flag_2     | 必要参数 | 参数介绍 |
| ---- | ------ | ------ | ---------- | -------- | -------- |
| 1    | job_id | `-j`   | `--job_id` | 是       | Job ID   |

-   *示例*：

``` bash
flow model tag-list -j $JOB_ID
```

### `tag-model`

-   *介绍*： 对模型添加标签。
-   *参数*：

| 编号 | 参数     | Flag_1 | Flag_2       | 必要参数 | 参数介绍                                               |
| ---- | -------- | ------ | ------------ | -------- | ------------------------------------------------------ |
| 1    | job_id   | `-j`   | `--job_id`   | 是       | Job ID                                                 |
| 2    | tag_name | `-t`   | `--tag-name` | 是       | 标签名                                                 |
| 3    | remove   |        | `--remove`   | 否       | 如果指定，带有指定标签名的标签将被模型的标签列表中移除 |

-   *示例*：

``` bash
flow model tag-model -j $JOB_ID -t $TAG_NAME
flow model tag-model -j $JOB_ID -t $TAG_NAME --remove
```

### `deploy`

-   *介绍*： 配置模型预测DSL。
-   *参数*：

| 编号 | 参数          | Flag_1 | Flag_2            | 必要参数 | 参数介绍                |
| ---- | ------------- | ------ | ----------------- | -------- | ----------------------- |
| 1    | model_id      |        | `--model-id`      | 是       | 模型ID                  |
| 2    | model_version |        | `--model-version` | 是       | 模型版本                |
| 3    | cpn_list      |        | `--cpn-list`      | 否       | 组件列表                |
| 4    | cpn_path      |        | `--cpn-path`      | 否       | 组件列表文件路径        |
| 5    | dsl_path      |        | `--dsl-path`      | 否       | 用户指定预测DSL文件路径 |

-   *示例*：

``` bash
flow model deploy --model-id $MODEL_ID --model-version $MODEL_VERSION
```

### `get-predict-dsl`

-   *介绍*： 获取模型预测DSL。
-   *参数*：

| 编号 | 参数          | Flag_1 | Flag_2            | 必要参数 | 参数介绍 |
| ---- | ------------- | ------ | ----------------- | -------- | -------- |
| 1    | model_id      |        | `--model-id`      | 是       | 模型ID   |
| 2    | model_version |        | `--model-version` | 是       | 模型版本 |
| 3    | output_path   | `-o`   | `--output-path`   | 是       | 输出路径 |

-   *示例*：

``` bash
flow model get-predict-dsl --model-id $MODEL_ID --model-version $MODEL_VERSION -o ./examples/
```

### `get-predict-conf`

-   *介绍*： 获取模型预测Conf模板。
-   *参数*：

| 编号 | 参数          | Flag_1 | Flag_2            | 必要参数 | 参数介绍 |
| ---- | ------------- | ------ | ----------------- | -------- | -------- |
| 1    | model_id      |        | `--model-id`      | 是       | 模型ID   |
| 2    | model_version |        | `--model-version` | 是       | 模型版本 |
| 3    | output_path   | `-o`   | `--output-path`   | 是       | 输出路径 |

-   *示例*：

``` bash
flow model get-predict-conf --model-id $MODEL_ID --model-version $MODEL_VERSION -o ./examples/
```

### `get-model-info`

-   *介绍*： 获取模型信息。
-   *参数*：

| 编号 | 参数          | Flag_1 | Flag_2            | 必要参数 | 参数介绍                 |
| ---- | ------------- | ------ | ----------------- | -------- | ------------------------ |
| 1    | model_id      |        | `--model-id`      | 否       | 模型ID                   |
| 2    | model_version |        | `--model-version` | 是       | 模型版本                 |
| 2    | role          | `-r`   | `--role`          | 否       | 角色                     |
| 3    | party_id      | `-p`   | `--party-id`      | 否       | Party ID                 |
| 3    | detail        |        | `--detail`        | 否       | 若指定，详细信息将被展示 |

-   *示例*：

``` bash
flow model get-model-info --model-id $MODEL_ID --model-version $MODEL_VERSION
flow model get-model-info --model-id $MODEL_ID --model-version $MODEL_VERSION --detail
```

## 9. Table

### `info`

**简要描述：** 

- 用于查询fate表的相关信息(真实存储地址,数量,schema等)

**请求CLI** 

- `flow table info -t $name -n $namespace`

**请求参数** 

| 参数名    | 必选 | 类型   | 说明           |
| :-------- | :--- | :----- | -------------- |
| name      | 是   | string | fate表名       |
| namespace | 是   | string | fate表命名空间 |

**返回参数** 

| 参数名  | 类型   | 说明     |
| :------ | :----- | -------- |
| retcode | int    | 返回码   |
| retmsg  | string | 返回信息 |
| data    | object | 返回数据 |

样例

```json
{
    "data": {
        "address": {
            "home": null,
            "name": "breast_hetero_guest",
            "namespace": "experiment"
        },
        "count": 569,
        "exist": 1,
        "namespace": "experiment",
        "partition": 4,
        "schema": {
            "header": "y,x0,x1,x2,x3,x4,x5,x6,x7,x8,x9",
            "sid": "id"
        },
        "table_name": "breast_hetero_guest"
    },
    "retcode": 0,
    "retmsg": "success"
}
```


### `delete`

**简要描述：** 
- 可通过table delete删除表数据

**请求CLI** 
- `flow table delete -t $name -n $namespace`

**请求参数** 

| 参数名    | 必选 | 类型   | 说明           |
| :-------- | :--- | :----- | -------------- |
| name      | 是   | string | fate表名       |
| namespace | 是   | string | fate表命名空间 |

**返回参数** 

| 参数名  | 类型   | 说明     |
| :------ | :----- | -------- |
| retcode | int    | 返回码   |
| retmsg  | string | 返回信息 |
| data    | object | 返回数据 |

样例

```json
{
    "data": {
        "namespace": "xxx",
        "table_name": "xxx"
    },
    "retcode": 0,
    "retmsg": "success"
}
```

### `bind`
**简要描述：** 

- 可通过table bind将真实存储地址映射到fate存储表

**请求CLI** 
- `flow table bind -c $conf_path`

注: conf_path为参数路径，具体参数如下

**请求参数** 

| 参数名         | 必选 | 类型   | 说明                                  |
| :------------- | :--- | :----- | ------------------------------------- |
| name           | 是   | string | fate表名                              |
| namespace      | 是   | string | fate表命名空间                        |
| engine         | 是   | string | 存储引擎, 支持"HDFS", "MYSQL", "PATH" |
| adress         | 是   | object | 真实存储地址                          |
| drop           | 否   | int    | 覆盖以前的信息                        |
| head           | 否   | int    | 是否有数据表头                        |
| id_delimiter   | 否   | string | 数据分隔符                            |
| id_column      | 否   | string | id字段                                |
| feature_column | 否   | array  | 特征字段                              |

**样例** 

- hdfs

```json
{
    "namespace": "experiment",
    "name": "breast_hetero_guest",
    "engine": "HDFS",
    "address": {
        "name_node": "hdfs://fate-cluster",
        "path": "/data/breast_hetero_guest.csv"
    },
    "id_delimiter": ",",
    "head": 1,
    "partitions": 10
}
```

- mysql

```json
{
  "engine": "MYSQL",
  "address": {
    "user": "fate",
    "passwd": "fate",
    "host": "127.0.0.1",
    "port": 3306,
    "db": "experiment",
    "name": "breast_hetero_guest"
  },
  "namespace": "experiment",
  "name": "breast_hetero_guest",
  "head": 1,
  "id_delimiter": ",",
  "partitions": 10,
  "id_column": "id",
  "feature_column": "y,x0,x1,x2,x3,x4,x5,x6,x7,x8,x9"
}
```

- PATH

```json
{
    "namespace": "xxx",
    "name": "xxx",
    "engine": "PATH",
    "address": {
        "path": "xxx"
    }
}
```

## 10. Task

### `query`

-   *介绍*： 检索Task信息。
-   *参数*：

| 编号 | 参数           | Flag_1 | Flag_2             | 必要参数 | 参数介绍 |
| ---- | -------------- | ------ | ------------------ | -------- | -------- |
| 1    | job_id         | `-j`   | `--job_id`         | 否       | Job ID   |
| 2    | role           | `-r`   | `--role`           | 否       | 角色     |
| 3    | party_id       | `-p`   | `--party_id`       | 否       | Party ID |
| 4    | component_name | `-cpn` | `--component_name` | 否       | 组件名   |
| 5    | status         | `-s`   | `--status`         | 否       | 任务状态 |

-   *示例*：

``` bash
flow task query -j $JOB_ID -p 9999 -r guest
flow task query -cpn hetero_feature_binning_0 -s complete
```

### `list`

-   *介绍*： 展示Task列表。
-   *参数*：

| 编号 | 参数  | Flag_1 | Flag_2    | 必要参数 | 参数介绍                     |
| ---- | ----- | ------ | --------- | -------- | ---------------------------- |
| 1    | limit | `-l`   | `--limit` | 否       | 返回结果数量限制（默认：10） |

-   *示例*：

``` bash
flow task list
flow task list -l 25
```

## 11. Tag

### `create`

-   *介绍*： 创建标签。
-   *参数*：

| 编号 | 参数         | Flag_1 | Flag_2       | 必要参数 | 参数介绍 |
| ---- | ------------ | ------ | ------------ | -------- | -------- |
| 1    | tag_name     | `-t`   | `--tag-name` | 是       | 标签名   |
| 2    | tag_参数介绍 | `-d`   | `--tag-desc` | 否       | 标签介绍 |

-   *示例*：

``` bash
flow tag create -t tag1 -d "This is the 参数介绍 of tag1."
flow tag create -t tag2
```

### `update`

-   *介绍*： 更新标签信息。
-   *参数*：

| 编号 | 参数         | Flag_1 | Flag_2           | 必要参数 | 参数介绍   |
| ---- | ------------ | ------ | ---------------- | -------- | ---------- |
| 1    | tag_name     | `-t`   | `--tag-name`     | 是       | 标签名     |
| 2    | new_tag_name |        | `--new-tag-name` | 否       | 新标签名   |
| 3    | new_tag_desc |        | `--new-tag-desc` | 否       | 新标签介绍 |

-   *示例*：

``` bash
flow tag update -t tag1 --new-tag-name tag2
flow tag update -t tag1 --new-tag-desc "This is the new 参数介绍."
```

### `list`

-   *介绍*： 展示标签列表。
-   *参数*：

| 编号 | 参数  | Flag_1 | Flag_2    | 必要参数 | 参数介绍                     |
| ---- | ----- | ------ | --------- | -------- | ---------------------------- |
| 1    | limit | `-l`   | `--limit` | 否       | 返回结果数量限制（默认：10） |

-   *示例*：

``` bash
flow tag list
flow tag list -l 3
```

### `query`

-   *介绍*： 检索标签。
-   *参数*：

| 编号 | 参数       | Flag_1 | Flag_2         | 必要参数 | 参数介绍                               |
| ---- | ---------- | ------ | -------------- | -------- | -------------------------------------- |
| 1    | tag_name   | `-t`   | `--tag-name`   | 是       | 标签名                                 |
| 2    | with_model |        | `--with-model` | 否       | 如果指定，具有该标签的模型信息将被展示 |

-   *示例*：

``` bash
flow tag query -t $TAG_NAME
flow tag query -t $TAG_NAME --with-model
```

### `delete`

-   *介绍*： 删除标签。
-   *参数*：

| 编号 | 参数     | Flag_1 | Flag_2       | 必要参数 | 参数介绍 |
| ---- | -------- | ------ | ------------ | -------- | -------- |
| 1    | tag_name | `-t`   | `--tag-name` | 是       | 标签名   |

-   *示例*：

``` bash
flow tag delete -t tag1
```

## 12. resource

### 12.1 资源查询

**请求CLI** 

```bash
flow resource query
```

**简要描述：** 

- 用于查询fate系统资源

**请求参数** 

无

**返回参数** 

| 参数名  | 类型   | 说明     |
| :------ | :----- | -------- |
| retcode | int    | 返回码   |
| retmsg  | string | 返回信息 |
| data    | object | 返回数据 |

样例：

```
{
    "data": {
        "computing_engine_resource": {
            "f_cores": 32,
            "f_create_date": "2021-09-21 19:32:59",
            "f_create_time": 1632223979564,
            "f_engine_config": {
                "cores_per_node": 32,
                "nodes": 1
            },
            "f_engine_entrance": "fate_on_eggroll",
            "f_engine_name": "EGGROLL",
            "f_engine_type": "computing",
            "f_memory": 0,
            "f_nodes": 1,
            "f_remaining_cores": 32,
            "f_remaining_memory": 0,
            "f_update_date": "2021-11-08 16:56:38",
            "f_update_time": 1636361798812
        },
        "use_resource_job": []
    },
    "retcode": 0,
    "retmsg": "success"
}
```

### 12.2 资源归还

**请求CLI** 

```bash
flow resource return -j $JobId
```

**简要描述：** 

- 用于归还某个job的资源

**请求参数** 

| 参数名 | 必选 | 类型   | 说明   |
| :----- | :--- | :----- | ------ |
| job_id | 是   | string | 任务id |

**返回参数** 

| 参数名  | 类型   | 说明     |
| :------ | :----- | -------- |
| retcode | int    | 返回码   |
| retmsg  | string | 返回信息 |
| data    | object | 返回数据 |

样例：

```json
{
    "data": [
        {
            "job_id": "202111081612427726750",
            "party_id": "8888",
            "resource_in_use": true,
            "resource_return_status": true,
            "role": "guest"
        }
    ],
    "retcode": 0,
    "retmsg": "success"
}
```

##13 privilege
## 13.1 授权

**简要描述：** 

- 添加权限

**请求CLI** 

- `flow privilege grant --src-party-id 9999  --src-role guest --privilege-role all --privilege-command all --privilege-component all`

**请求参数** 

| 参数名              | 必选 | 类型   | 说明                                                         |
| :------------------ | :--- | :----- | ------------------------------------------------------------ |
| src-party-id        | 是   | string | 发起方partyid                                                |
| src-role            | 是   | string | 发起方role                                                   |
| privilege-role      | 否   | string | guest, host, arbiter，all, 其中all为全部权限都给予           |
| privilege-command   | 否   | string | ”stop”, “run”, “create”, all, 其中all为全部权限都给予        |
| privilege-component | 否   | string | 算法组件的小写,如dataio,heteronn等等, 其中all为全部权限都给予 |

**样例** 

- 赋予role权限

  ```shell
  flow privilege grant --src-party-id 9999  --src-role guest --privilege-role all
  ```
  
- 赋予command权限

  ```shell
  flow privilege grant --src-party-id 9999  --src-role guest --privilege-command all
  ```
  
- 赋予component权限

  ```shell
  flow privilege grant --src-party-id 9999  --src-role guest --privilege-component all
  ```

- 同时赋予多种权限

  ```shell
  flow privilege grant --src-party-id 9999  --src-role guest --privilege-role all --privilege-command all --privilege-component all
  ```

  

**返回参数** 

| 参数名  | 类型   | 说明     |
| ------- | :----- | -------- |
| retcode | int    | 返回码   |
| retmsg  | string | 返回信息 |

**样例** 

```shell
{
    "retcode": 0,
    "retmsg": "success"
}
```



## 13.2 吊销权限

**简要描述：** 

- 删除权限

**请求CLI** 

- `flow privilege delete --src-party-id 9999  --src-role guest --privilege-role all --privilege-command all --privilege-component all`

**请求参数** 

| 参数名              | 必选 | 类型   | 说明                                                         |
| :------------------ | :--- | :----- | ------------------------------------------------------------ |
| src-party-id        | 是   | string | 发起方partyid                                                |
| src-role            | 是   | string | 发起方role                                                   |
| privilege-role      | 否   | string | guest, host, arbiter，all, 其中all为全部权限都撤销           |
| privilege-command   | 否   | string | ”stop”, “run”, “create”, all, 其中all为全部权限都撤销        |
| privilege-component | 否   | string | 算法组件的小写,如dataio,heteronn等等, 其中all为全部权限都撤销 |

**样例** 

- 撤销role权限

  ```shell
  flow privilege delete --src-party-id 9999  --src-role guest --privilege-role all
  ```

- 撤销command权限

  ```shell
  flow privilege delete --src-party-id 9999  --src-role guest --privilege-command all
  ```

- 撤销component权限

  ```shell
  flow privilege delete --src-party-id 9999  --src-role guest --privilege-component all
  ```

- 同时赋予多种权限

  ```shell
  flow privilege delete --src-party-id 9999  --src-role guest --privilege-role all --privilege-command all --privilege-component all
  ```

**返回参数** 

| 参数名  | 类型   | 说明     |
| ------- | :----- | -------- |
| retcode | int    | 返回码   |
| retmsg  | string | 返回信息 |

**样例** 

```shell
{
    "retcode": 0,
    "retmsg": "success"
}
```



## 13.3 权限查询

**简要描述：** 

- 查询权限

**请求CLI** 

- `flow privilege query --src-party-id 9999  --src-role guest`

**请求参数** 

| 参数名       | 必选 | 类型   | 说明          |
| :----------- | :--- | :----- | ------------- |
| src-party-id | 是   | string | 发起方partyid |
| src-role     | 是   | string | 发起方role    |

**样例** 

```shell
flow privilege query --src-party-id 9999  --src-role guest 
```

- **返回参数** 


| 参数名  | 类型   | 说明     |
| ------- | :----- | -------- |
| retcode | int    | 返回码   |
| retmsg  | string | 返回信息 |
| data    | object | 返回数据 |

**样例** 

```shell
{
    "data": {
        "privilege_command": [],
        "privilege_component": [],
        "privilege_role": [],
        "role": "guest",
        "src_party_id": "9999"
    },
    "retcode": 0,
    "retmsg": "success"
}

```

