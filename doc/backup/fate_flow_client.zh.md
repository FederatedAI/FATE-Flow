# FATE Flow 客户端

[TOC]

## 1. 说明

- 介绍如何安装使用`FATE Flow Client`，其通常包含在`FATE Client`中，`FATE Client`包含了`FATE项目`多个客户端：`Pipeline`, `FATE Flow Client` 和 `FATE Test`
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

- 介绍所有命令使用说明

## 2. 安装FATE Client

### 在线安装

FATE Client会发布到`pypi`，可直接使用`pip`等工具安装对应版本，如

```bash
pip install fate-client
```

或者

```bash
pip install fate-client==${version}
```

### 在FATE集群上安装

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

### 指定fateflow服务地址

```bash
# 指定fateflow的IP地址和端口进行初始化
flow init --ip 192.168.0.1 --port 9380
```

### 通过FATE集群上的配置文件

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

## 5. Data

### upload

用于上传建模任务的输入数据到fate所支持的存储系统

```bash
flow data upload -c ${conf_path}
```

注: conf_path为参数路径，具体参数如下

**参数** 

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

### download

**简要描述：** 

用于下载fate存储引擎内的数据到文件格式数据

```bash
flow data download -c ${conf_path}
```

注: conf_path为参数路径，具体参数如下

**参数** 

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

## 6. Table

### info

用于查询fate表的相关信息(真实存储地址,数量,schema等)

```bash
flow table info [options]
```

**参数** 

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

### delete

可通过table delete删除表数据

```bash
flow table delete [options]
```

**参数** 

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

### bind

可通过table bind将真实存储地址映射到fate存储表

```bash
flow table bind [options]
```

注: conf_path为参数路径，具体参数如下

**参数** 

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

## 7. Job

### submit

通过两个配置文件：job dsl和job conf构建一个联邦学习作业，提交到调度系统执行

```bash
flow job submit [options]
```

**参数** 

| 参数名          | 必选 | 类型   | 说明           |
| :-------------- | :--- | :----- | -------------- |
| -d, --dsl-path  | 是   | string | job dsl的路径  |
| -c, --conf-path | 是   | string | job conf的路径 |


**返回参数** 

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

**参数** 

| 参数名                 | 必选 | 类型   | 说明                                                                                                  |
| :--------------------- | :--- | :----- | ----------------------------------------------------------------------------------------------------- |
| -j, --job-id           | 是   | string | job id 路径                                                                                           |
| -cpn, --component-name | 否   | string | 指定从哪个组件重跑，没被指定的组件若与指定组件没有上游依赖关系则不会执行;若不指定该参数则整个作业重跑 |
| --force                | 否   | bool   | 作业即使成功也重跑;若不指定该参数，作业如果成功，则跳过重跑                                           |

**返回参数** 

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

**参数** 

| 参数名          | 必选 | 类型   | 说明                                                 |
| :-------------- | :--- | :----- | ---------------------------------------------------- |
| -j, --job-id    | 是   | string | job id 路径                                          |
| -c, --conf-path | 是   | string | 需要更新的job conf的内容，不需要更新的参数不需要填写 |

**返回参数** 

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

-   *参数*：

| 编号 | 参数   | 短格式 | 长格式     | 必要参数 | 参数介绍 |
| ---- | ------ | ------ | ---------- | -------- | -------- |
| 1    | job_id | `-j`   | `--job_id` | 是       | Job ID   |

-   *示例*：

    ``` bash
    flow job stop -j $JOB_ID
    ```

### query

-   *介绍*： 检索任务信息。
-   *参数*：

| 编号 | 参数     | 短格式 | 长格式       | 必要参数 | 参数介绍 |
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

### view

-   *介绍*： 检索任务数据视图。
-   *参数*：

| 编号 | 参数     | 短格式 | 长格式       | 必要参数 | 参数介绍 |
| ---- | -------- | ------ | ------------ | -------- | -------- |
| 1    | job_id   | `-j`   | `--job_id`   | 是       | Job ID   |
| 2    | role     | `-r`   | `--role`     | 否       | 角色     |
| 3    | party_id | `-p`   | `--party_id` | 否       | Party ID |
| 4    | status   | `-s`   | `--status`   | 否       | 任务状态 |

-   *示例*：

    ``` bash
    flow job view -j $JOB_ID -s complete
    ```

### config

-   *介绍*： 下载指定任务的配置文件到指定目录。
-   *参数*：

| 编号 | 参数        | 短格式 | 长格式          | 必要参数 | 参数介绍 |
| ---- | ----------- | ------ | --------------- | -------- | -------- |
| 1    | job_id      | `-j`   | `--job_id`      | 是       | Job ID   |
| 2    | role        | `-r`   | `--role`        | 是       | 角色     |
| 3    | party_id    | `-p`   | `--party_id`    | 是       | Party ID |
| 4    | output_path | `-o`   | `--output-path` | 是       | 输出目录 |

-   *示例*：

    ``` bash
    flow job config -j $JOB_ID -r host -p 10000 --output-path ./examples/
    ```

### log

-   *介绍*： 下载指定任务的日志文件到指定目录。
-   *参数*：

| 编号 | 参数        | 短格式 | 长格式          | 必要参数 | 参数介绍 |
| ---- | ----------- | ------ | --------------- | -------- | -------- |
| 1    | job_id      | `-j`   | `--job_id`      | 是       | Job ID   |
| 2    | output_path | `-o`   | `--output-path` | 是       | 输出目录 |

-   *示例*：

    ``` bash
    flow job log -j JOB_ID --output-path ./examples/
    ```

### list

-   *介绍*： 展示任务列表。
-   *参数*：

| 编号 | 参数  | 短格式 | 长格式    | 必要参数 | 参数介绍                 |
| ---- | ----- | ------ | --------- | -------- | ------------------------ |
| 1    | limit | `-l`   | `--limit` | 否       | 返回数量限制（默认：10） |

-   *示例*：

``` bash
flow job list
flow job list -l 30
```

### dsl

-   *介绍*： 预测DSL文件生成器。
-   *参数*：

| 编号 | 参数           | 短格式 | 长格式             | 必要参数 | 参数介绍                         |
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

## 8. Task

### query

检索Task信息

-   *参数*：

| 编号 | 参数           | 短格式 | 长格式             | 必要参数 | 参数介绍 |
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

### list

-   *介绍*： 展示Task列表。
-   *参数*：

| 编号 | 参数  | 短格式 | 长格式    | 必要参数 | 参数介绍                     |
| ---- | ----- | ------ | --------- | -------- | ---------------------------- |
| 1    | limit | `-l`   | `--limit` | 否       | 返回结果数量限制（默认：10） |

-   *示例*：

``` bash
flow task list
flow task list -l 25
```

## 9. Tracking

### metrics

获取某个组件任务产生的所有指标名称列表

```bash
flow tracking metrics [options]
```

**参数** 

| 参数名                 | 必选 | 类型   | 说明                          |
| :--------------------- | :--- | :----- | ----------------------------- |
| -j, --job-id           | 是   | string | 作业id                        |
| -r, --role             | 是   | string | 参与角色                      |
| -p, --partyid          | 是   | string | 参与方id                      |
| -cpn, --component-name | 是   | string | 组件名，与job dsl中的保持一致 |

**返回参数** 

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

**参数** 

| 参数名                 | 必选 | 类型   | 说明                          |
| :--------------------- | :--- | :----- | ----------------------------- |
| -j, --job-id           | 是   | string | 作业id                        |
| -r, --role             | 是   | string | 参与角色                      |
| -p, --partyid          | 是   | string | 参与方id                      |
| -cpn, --component-name | 是   | string | 组件名，与job dsl中的保持一致 |

**返回参数** 

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

**参数** 

| 参数名                 | 必选 | 类型   | 说明                          |
| :--------------------- | :--- | :----- | ----------------------------- |
| -j, --job-id           | 是   | string | 作业id                        |
| -r, --role             | 是   | string | 参与角色                      |
| -p, --partyid          | 是   | string | 参与方id                      |
| -cpn, --component-name | 是   | string | 组件名，与job dsl中的保持一致 |


**返回参数** 

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

**参数** 

| 参数名                 | 必选 | 类型   | 说明                          |
| :--------------------- | :--- | :----- | ----------------------------- |
| -j, --job-id           | 是   | string | 作业id                        |
| -r, --role             | 是   | string | 参与角色                      |
| -p, --partyid          | 是   | string | 参与方id                      |
| -cpn, --component-name | 是   | string | 组件名，与job dsl中的保持一致 |
| -o, --output-path      | 是   | string | 输出数据的存放路径            |

**返回参数** 

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

**参数** 

| 参数名                 | 必选 | 类型   | 说明                          |
| :--------------------- | :--- | :----- | ----------------------------- |
| -j, --job-id           | 是   | string | 作业id                        |
| -r, --role             | 是   | string | 参与角色                      |
| -p, --partyid          | 是   | string | 参与方id                      |
| -cpn, --component-name | 是   | string | 组件名，与job dsl中的保持一致 |

**返回参数** 

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

**参数** 

| 参数名                 | 必选 | 类型   | 说明                          |
| :--------------------- | :--- | :----- | ----------------------------- |
| -j, --job-id           | 是   | string | 作业id                        |
| -r, --role             | 是   | string | 参与角色                      |
| -p, --partyid          | 是   | string | 参与方id                      |
| -cpn, --component-name | 是   | string | 组件名，与job dsl中的保持一致 |

**返回参数** 

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

**参数** 

| 参数名                 | 必选 | 类型   | 说明                          |
| :--------------------- | :--- | :----- | ----------------------------- |
| -j, --job-id           | 是   | string | 作业id                        |
| -r, --role             | 是   | string | 参与角色                      |
| -p, --partyid          | 是   | string | 参与方id                      |
| -cpn, --component-name | 是   | string | 组件名，与job dsl中的保持一致 |

**返回参数** 

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

**参数** 

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

样例：

```json
{
    "data": [{"parent_table_name": "61210fa23c8d11ec849a5254004fdc71", "parent_table_namespace": "output_data_202111031759294631020_hetero_lr_0_0", "source_table_name": "breast_hetero_guest", "source_table_namespace": "experiment"}],
    "retcode": 0,
    "retmsg": "success"
}
```

### tracking-job

用于查询某张表的使用情况

**请求CLI** 

```bash
flow table tracking-job [options]
```

**参数** 

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

样例:

```json
{
    "data": {"count":2,"job":["202111052115375327830", "202111031816501123160"]},
    "retcode": 0,
    "retmsg": "success"
}
```

## 10. Model

### load

向 Fate-Serving 加载 `deploy` 生成的模型。

```bash
flow model load -c examples/model/publish_load_model.json
flow model load -c examples/model/publish_load_model.json -j <job_id>
```

**参数**

| 参数      | 短格式 | 长格式        | 可选参数 | 说明     |
| --------- | ------ | ------------- | -------- | -------- |
| conf_path | `-c`   | `--conf-path` | 否       | 配置文件 |
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

**参数**

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

**参数**

| 参数          | 短格式 | 长格式            | 可选参数 | 说明                             |
| ------------- | ------ | ----------------- | -------- | -------------------------------- |
| conf_path     | `-c`   | `--conf-path`     | 否       | 配置文件                         |
| from_database |        | `--from-database` | 是       | 从 Flow 配置的存储引擎中导入模型 |

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

**参数**

| 参数        | 短格式 | 长格式          | 可选参数 | 说明                               |
| ----------- | ------ | --------------- | -------- | ---------------------------------- |
| conf_path   | `-c`   | `--conf-path`   | 否       | 配置文件                           |
| to_database |        | `--to-database` | 是       | 将模型导出到 Flow 配置的存储引擎中 |

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

迁移模型

```bash
flow model migrate -c examples/model/migrate_model.json
```

**参数**

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

获取模型的标签列表

``` bash
flow model tag-list -j <job_id>
```

**参数**

| 参数   | 短格式 | 长格式     | 可选参数 | 说明    |
| ------ | ------ | ---------- | -------- | ------- |
| job_id | `-j`   | `--job_id` | 否       | 任务 ID |

### tag-model

向模型添加标签

```bash
flow model tag-model -j <job_id> -t <tag_name>
flow model tag-model -j <job_id> -t <tag_name> --remove
```

**参数**

| 参数     | 短格式 | 长格式       | 可选参数 | 说明           |
| -------- | ------ | ------------ | -------- | -------------- |
| job_id   | `-j`   | `--job_id`   | 否       | 任务 ID        |
| tag_name | `-t`   | `--tag-name` | 否       | 标签名         |
| remove   |        | `--remove`   | 是       | 移除指定的标签 |

### deploy

配置预测 DSL

```bash
flow model deploy --model-id <model_id> --model-version <model_version>
```

**参数**

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

**参数**

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

**参数**

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

**参数**

| 参数          | 短格式 | 长格式            | 可选参数 | 说明         |
| ------------- | ------ | ----------------- | -------- | ------------ |
| model_id      |        | `--model-id`      | 否       | 模型 ID      |
| model_version |        | `--model-version` | 否       | 模型版本     |
| role          | `-r`   | `--role`          | 是       | Party 角色   |
| party_id      | `-p`   | `--party-id`      | 是       | Party ID     |
| detail        |        | `--detail`        | 是       | 展示详细信息 |

### homo-convert

基于横向训练的模型，生成其他 ML  框架的模型文件。

```bash
flow model homo-convert -c examples/model/homo_convert_model.json
```

**参数**

| 参数      | 短格式 | 长格式        | 可选参数 | 说明     |
| --------- | ------ | ------------- | -------- | -------- |
| conf_path | `-c`   | `--conf-path` | 否       | 配置文件 |

### homo-deploy

将横向训练后使用 `homo-convert` 生成的模型部署到在线推理系统中，当前支持创建基于 KFServing 的推理服务。

```bash
flow model homo-deploy -c examples/model/homo_deploy_model.json
```

**参数**

| 参数      | 短格式 | 长格式        | 可选参数 | 说明             |
| --------- | ------ | ------------- | -------- | ---------------- |
| conf_path | `-c`   | `--conf-path` | 否       | 任务配置文件路径 |

## 11. Checkpoint

### list

获取 Checkpoint 模型列表。

```bash
flow checkpoint list --model-id <model_id> --model-version <model_version> --role <role> --party-id <party_id> --component-name <component_name>
```

**参数**

| 参数           | 短格式 | 长格式             | 可选参数 | 说明       |
| -------------- | ------ | ------------------ | -------- | ---------- |
| model_id       |        | `--model-id`       | 否       | 模型 ID    |
| model_version  |        | `--model-version`  | 否       | 模型版本   |
| role           | `-r`   | `--role`           | 否       | Party 角色 |
| party_id       | `-p`   | `--party-id`       | 否       | Party ID   |
| component_name | `-cpn` | `--component-name` | 否       | 组件名     |

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

### get

获取 Checkpoint 模型信息。

```bash
flow checkpoint get --model-id <model_id> --model-version <model_version> --role <role> --party-id <party_id> --component-name <component_name> --step-index <step_index>
```


**参数**

| 参数           | 短格式 | 长格式             | 可选参数 | 说明                                  |
| -------------- | ------ | ------------------ | -------- | ------------------------------------- |
| model_id       |        | `--model-id`       | 否       | 模型 ID                               |
| model_version  |        | `--model-version`  | 否       | 模型版本                              |
| role           | `-r`   | `--role`           | 否       | Party 角色                            |
| party_id       | `-p`   | `--party-id`       | 否       | Party ID                              |
| component_name | `-cpn` | `--component-name` | 否       | 组件名                                |
| step_index     |        | `--step-index`     | 是       | Step index，不可与 step_name 同时使用 |
| step_name      |        | `--step-name`      | 是       | Step name，不可与 step_index 同时使用 |

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

## 12. Provider

### list

列出当前所有组件提供者及其提供组件信息

```bash
flow provider list [options]
```

**参数** 

**返回参数** 

| 参数名  | 类型   | 说明     |
| :------ | :----- | -------- |
| retcode | int    | 返回码   |
| retmsg  | string | 返回信息 |
| data    | dict   | 返回数据 |

**样例** 

输出:

```json
{
    "data": {
        "fate": {
            "1.7.0": {
                "class_path": {
                    "feature_instance": "feature.instance.Instance",
                    "feature_vector": "feature.sparse_vector.SparseVector",
                    "homo_model_convert": "protobuf.homo_model_convert.homo_model_convert",
                    "interface": "components.components.Components",
                    "model": "protobuf.generated",
                    "model_migrate": "protobuf.model_migrate.model_migrate"
                },
                "components": [
                    "heterolinr",
                    "homoonehotencoder",
                    "dataio",
                    "psi",
                    "homodatasplit",
                    "homolr",
                    "columnexpand",
                    "heterokmeans",
                    "heterosshelr",
                    "homosecureboost",
                    "heteropoisson",
                    "featureimputation",
                    "heterofeatureselection",
                    "heteropearson",
                    "heterodatasplit",
                    "ftl",
                    "heterolr",
                    "homonn",
                    "evaluation",
                    "featurescale",
                    "intersection",
                    "heteronn",
                    "datastatistics",
                    "heterosecureboost",
                    "sbtfeaturetransformer",
                    "datatransform",
                    "heterofeaturebinning",
                    "feldmanverifiablesum",
                    "heterofastsecureboost",
                    "federatedsample",
                    "secureaddexample",
                    "secureinformationretrieval",
                    "sampleweight",
                    "union",
                    "onehotencoder",
                    "homofeaturebinning",
                    "scorecard",
                    "localbaseline",
                    "labeltransform"
                ],
                "path": "${FATE_PROJECT_BASE}/python/federatedml",
                "python": ""
            },
            "default": {
                "version": "1.7.0"
            }
        },
        "fate_flow": {
            "1.7.0": {
                "class_path": {
                    "feature_instance": "feature.instance.Instance",
                    "feature_vector": "feature.sparse_vector.SparseVector",
                    "homo_model_convert": "protobuf.homo_model_convert.homo_model_convert",
                    "interface": "components.components.Components",
                    "model": "protobuf.generated",
                    "model_migrate": "protobuf.model_migrate.model_migrate"
                },
                "components": [
                    "download",
                    "upload",
                    "modelloader",
                    "reader",
                    "modelrestore",
                    "cacheloader",
                    "modelstore"
                ],
                "path": "${FATE_FLOW_BASE}/python/fate_flow",
                "python": ""
            },
            "default": {
                "version": "1.7.0"
            }
        }
    },
    "retcode": 0,
    "retmsg": "success"
}
```

包含`组件提供者`的`名称`, `版本号`, `代码路径`, `提供的组件列表`

### register

注册一个组件提供者

```bash
flow provider register [options]
```

**参数** 

| 参数名                 | 必选 | 类型   | 说明                             |
| :--------------------- | :--- | :----- | ------------------------------|
| -c, --conf-path          | 是   | string | 配置路径                         |

**返回参数** 

| 参数名  | 类型   | 说明     |
| :------ | :----- | -------- |
| retcode | int    | 返回码   |
| retmsg  | string | 返回信息 |

**样例** 

```bash
flow provider register -c $FATE_FLOW_BASE/examples/other/register_provider.json
```

配置文件：

```json
{
  "name": "fate",
  "version": "1.7.1",
  "path": "${FATE_FLOW_BASE}/python/component_plugins/fateb/python/federatedml"
}
```

输出:

```json
{
    "retcode": 0,
    "retmsg": "success"
}
```

## 13. resource

### query

用于查询fate系统资源

```bash
flow resource query
```

**参数** 

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

### return

用于归还某个job的资源

```bash
flow resource return [options]
```

**参数** 

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

## 14. privilege

### grant

添加权限

```bash
flow privilege grant [options]
```

**参数** 

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

### delete

删除权限

```bash
flow privilege delete [options]
```

**参数** 

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

### query

查询权限

```bash
flow privilege query [options]
```

**参数** 

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

## 15. Tag

### create

-   *介绍*： 创建标签。
-   *参数*：

| 编号 | 参数         | 短格式 | 长格式       | 必要参数 | 参数介绍 |
| ---- | ------------ | ------ | ------------ | -------- | -------- |
| 1    | tag_name     | `-t`   | `--tag-name` | 是       | 标签名   |
| 2    | tag_参数介绍 | `-d`   | `--tag-desc` | 否       | 标签介绍 |

-   *示例*：

``` bash
flow tag create -t tag1 -d "This is the 参数介绍 of tag1."
flow tag create -t tag2
```

### update

-   *介绍*： 更新标签信息。
-   *参数*：

| 编号 | 参数         | 短格式 | 长格式           | 必要参数 | 参数介绍   |
| ---- | ------------ | ------ | ---------------- | -------- | ---------- |
| 1    | tag_name     | `-t`   | `--tag-name`     | 是       | 标签名     |
| 2    | new_tag_name |        | `--new-tag-name` | 否       | 新标签名   |
| 3    | new_tag_desc |        | `--new-tag-desc` | 否       | 新标签介绍 |

-   *示例*：

``` bash
flow tag update -t tag1 --new-tag-name tag2
flow tag update -t tag1 --new-tag-desc "This is the new 参数介绍."
```

### list

-   *介绍*： 展示标签列表。
-   *参数*：

| 编号 | 参数  | 短格式 | 长格式    | 必要参数 | 参数介绍                     |
| ---- | ----- | ------ | --------- | -------- | ---------------------------- |
| 1    | limit | `-l`   | `--limit` | 否       | 返回结果数量限制（默认：10） |

-   *示例*：

``` bash
flow tag list
flow tag list -l 3
```

### query

-   *介绍*： 检索标签。
-   *参数*：

| 编号 | 参数       | 短格式 | 长格式         | 必要参数 | 参数介绍                               |
| ---- | ---------- | ------ | -------------- | -------- | -------------------------------------- |
| 1    | tag_name   | `-t`   | `--tag-name`   | 是       | 标签名                                 |
| 2    | with_model |        | `--with-model` | 否       | 如果指定，具有该标签的模型信息将被展示 |

-   *示例*：

``` bash
flow tag query -t $TAG_NAME
flow tag query -t $TAG_NAME --with-model
```

### delete

-   *介绍*： 删除标签。
-   *参数*：

| 编号 | 参数     | 短格式 | 长格式       | 必要参数 | 参数介绍 |
| ---- | -------- | ------ | ------------ | -------- | -------- |
| 1    | tag_name | `-t`   | `--tag-name` | 是       | 标签名   |

-   *示例*：

``` bash
flow tag delete -t tag1
```

## 16. Server

### versions

列出所有相关系统版本号

```bash
flow server
```

**参数** 

无

**返回参数** 

| 参数名  | 类型   | 说明     |
| :------ | :----- | -------- |
| retcode | int    | 返回码   |
| retmsg  | string | 返回信息 |
| data    | dict   | 返回数据 |
| jobId   | string | 作业id   |

**样例** 

```bash
flow server versions
```

输出:

```json
{
    "data": {
        "API": "v1",
        "CENTOS": "7.2",
        "EGGROLL": "2.4.0",
        "FATE": "1.7.0",
        "FATEBoard": "1.7.0",
        "FATEFlow": "1.7.0",
        "JDK": "8",
        "MAVEN": "3.6.3",
        "PYTHON": "3.6.5",
        "SPARK": "2.4.1",
        "UBUNTU": "16.04"
    },
    "retcode": 0,
    "retmsg": "success"
}
```

### reload

如下配置项在`reload`后会重新生效

  - $FATE_PROJECT_BASE/conf/service_conf.yaml中# engine services后的所有配置
  - $FATE_FLOW_BASE/python/fate_flow/job_default_config.yaml中所有配置

```bash
flow server reload
```

**参数** 

无

**返回参数** 

| 参数名  | 类型   | 说明     |
| :------ | :----- | -------- |
| retcode | int    | 返回码   |
| retmsg  | string | 返回信息 |
| data    | dict   | 返回数据 |
| jobId   | string | 作业id   |

**样例** 

```bash
flow server reload
```

输出:

```json
{
    "data": {
        "job_default_config": {
            "auto_retries": 0,
            "auto_retry_delay": 1,
            "default_component_provider_path": "component_plugins/fate/python/federatedml",
            "end_status_job_scheduling_time_limit": 300000,
            "end_status_job_scheduling_updates": 1,
            "federated_command_trys": 3,
            "federated_status_collect_type": "PUSH",
            "job_timeout": 259200,
            "max_cores_percent_per_job": 1,
            "output_data_summary_count_limit": 100,
            "remote_request_timeout": 30000,
            "task_cores": 4,
            "task_memory": 0,
            "task_parallelism": 1,
            "total_cores_overweight_percent": 1,
            "total_memory_overweight_percent": 1,
            "upload_max_bytes": 4194304000
        },
        "service_registry": null
    },
    "retcode": 0,
    "retmsg": "success"
}
```
