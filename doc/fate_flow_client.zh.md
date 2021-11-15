# FATE Flow 客户端

[TOC]

## 1. 说明

主要介绍如何安装使用`FATE Flow Client`，其通常包含在`FATE Client`中，`FATE Client`包含了`FATE项目`多个客户端：`Pipeline` `FATE Flow Client` `FATE Test`

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

-   *介绍*： 上传数据表。
-   *参数*：

| 编号 | 参数      | Flag_1 | Flag_2        | 必要参数 | 参数介绍                                                       |
| ---- | --------- | ------ | ------------- | -------- | -------------------------------------------------------------- |
| 1    | conf_path | `-c`   | `--conf-path` | 是       | 任务配置文件路径                                               |
| 2    | verbose   |        | `--verbose`   | 否       | 如果指定，用户将在控制台获得上传进度（默认不开启）             |
| 3    | drop      |        | `--drop`      | 否       | 如果指定，旧版已上传数据将被新上传的同名数据替换（默认不替换） |

-   *示例*：

``` bash
flow data upload -c fate_flow/examples/upload_guest.json
flow data upload -c fate_flow/examples/upload_host.json --verbose --drop
```

### `download`

-   *介绍*： 下载数据表。
-   *参数*：

| 编号 | 参数      | Flag_1 | Flag_2        | 必要参数 | 参数介绍         |
| ---- | --------- | ------ | ------------- | -------- | ---------------- |
| 1    | conf_path | `-c`   | `--conf-path` | 是       | 任务配置文件路径 |

-   *示例*：

``` bash
flow data download -c fate_flow/examples/download_host.json
```

### `upload-history`

-   *介绍*： 检索上传数据历史。
-   *参数*：

| 编号 | 参数   | Flag_1 | Flag_2     | 必要参数 | 参数介绍                     |
| ---- | ------ | ------ | ---------- | -------- | ---------------------------- |
| 1    | limit  | `-l`   | `--limit`  | 否       | 返回结果数量限制（默认：10） |
| 2    | job_id | `-j`   | `--job_id` | 否       | Job ID                       |

-   *示例*：

``` bash
flow data upload-history -l 20
flow data upload-history --job-id $JOB_ID
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

-   *介绍*： 检索数据表信息。
-   *参数*：

| 编号 | 参数       | Flag_1 | Flag_2         | 必要参数 | 参数介绍 |
| ---- | ---------- | ------ | -------------- | -------- | -------- |
| 1    | namespace  | `-n`   | `--namespace`  | 是       | 命名空间 |
| 2    | table_name | `-t`   | `--table-name` | 是       | 数据表名 |

-   *示例*：

``` bash
flow table info -n $NAMESPACE -t $TABLE_NAME
```

### `delete`

-   *介绍*： 删除指定数据表。
-   *参数*：

| 编号 | 参数       | Flag_1 | Flag_2         | 必要参数 | 参数介绍 |
| ---- | ---------- | ------ | -------------- | -------- | -------- |
| 1    | namespace  | `-n`   | `--namespace`  | 否       | 命名空间 |
| 2    | table_name | `-t`   | `--table_name` | 否       | 数据表名 |

-   *示例*：

``` bash
flow table delete -n $NAMESPACE -t $TABLE_NAME
```

### `add`

-   *介绍*： 绑定数据真实存储路径到fate表中
-   *参数*：

| 编号 | 参数      | Flag_1 | Flag_2        | 必要参数 | 参数介绍         |
| ---- | --------- | ------ | ------------- | -------- | ---------------- |
| 1    | conf_path | `-c`   | `--conf-path` | 是       | 任务配置文件路径 |

-   *示例*：

``` bash
flow table add -c $conf_path
```

### `bind`

-   *介绍*： 绑定数据真实存储路径到fate表中，同add；
-   *参数*：

| 编号 | 参数      | Flag_1 | Flag_2        | 必要参数 | 参数介绍         |
| ---- | --------- | ------ | ------------- | -------- | ---------------- |
| 1    | conf_path | `-c`   | `--conf-path` | 是       | 任务配置文件路径 |

-   *示例*：

``` bash
flow table bind -c $conf_path
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

## 12. Queue

### `clean`

-   *介绍*： 取消所有在队列中的Job。
-   *参数*： 无
-   *示例*：

``` bash
flow queue clean
```
