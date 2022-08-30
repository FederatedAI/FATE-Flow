## Data

### upload

用于上传建模任务的输入数据到fate所支持的存储系统

```bash
flow data upload -c ${conf_path}
```

注: conf_path为参数路径，具体参数如下

**选项** 

| 参数名                 | 必选  | 类型     | 说明                                              |
|:--------------------|:----|:-------|-------------------------------------------------|
| file                | 是   | string | 数据存储路径                                          |
| id_delimiter        | 是   | string | 数据分隔符,如","                                      |
| head                | 否   | int    | 数据是否有表头                                         |
| partition           | 是   | int    | 数据分区数                                           |
| storage_engine      | 否   | string | 存储引擎类型，默认"EGGROLL"，还支持"HDFS","LOCALFS", "HIVE"等 |
| namespace           | 是   | string | 表命名空间                                           |
| table_name          | 是   | string | 表名                                              |
| storage_address     | 否   | object | 需要填写对应存储引擎的存储地址                                 |
| use_local_data      | 否   | int    | 默认1，代表使用client机器的数据;0代表使用fate flow服务所在机器的数据     |
| drop                | 否   | int    | 是否覆盖上传                                          |
| extend_sid          | 否   | bool   | 是否新增一列uuid id，默认False                           |
| auto_increasing_sid | 否   | bool   | 新增的id列是否自增(extend_sid为True才会生效), 默认False        |
| with_meta           | 否   | bool   | 是否携带meta数据, 默认False                             |
| meta                | 否   | object | 元数据, 默认为空，with_meta为true生效                      |

**mete信息**

| 参数名                  | 必选  | 类型     | 说明                                        |
|:---------------------|:----|:-------|-------------------------------------------|
| input_format         | 否   | string | 数据格式(danse、svmlight、tag:value)，用来判断       |
| delimiter            | 否   | string | 数据分隔符,默认","                               |
| tag_with_value       | 否   | bool   | 对tag的数据格式生效，是否携带value                     |
| tag_value_delimiter  | 否   | string | tag:value数据分隔符，默认":"                      |
| with_match_id        | 否   | bool   | 是否携带match id                              |
| id_list              | 否   | object | id列名称，开启extend_sid下生效，如：["imei", "phone"] |
| id_range             | 否   | object | 对于tag/svmlight格式数据，哪几列为id                 |
| exclusive_data_type  | 否   | string | 特殊类型数据列格式                                 |
| data_type            | 否   | string | 列数据类型，默认"float64                          |
| with_label           | 否   | bool   | 是否有标签，默认False                             |
| label_name           | 否   | string | 标签名，默认"y"                                 |
| label_type           | 否   | string | 标签类型, 默认"int"                             |

**注意：在1.9.0及之后的版本中，若传入meta参数，会生成特征的匿名信息。**

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

**返回**

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

### upload-history

用于查询上传历史

```
flow data upload-history -l 20
flow data upload-history --job-id $JOB_ID
```

**选项**

| 参数名      | 必选 | 类型   | 说明                |
| :---------- | :--- | :----- | ------------------- |
| -l --limit  | no   | int    | 返回数量 (默认: 10) |
| -j --job_id | no   | string | 任务ID              |
|             |      |        |                     |

### download

**简要描述：** 

用于下载fate存储引擎内的数据到文件格式数据

```bash
flow data download -c ${conf_path}
```

注: conf_path为参数路径，具体参数如下

**选项** 

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

**返回**

| 参数名  | 类型   | 说明     |
| :------ | :----- | -------- |
| jobId | string | 任务id |
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

### writer

**简要描述：** 

用于下载fate存储引擎内的数据到外部引擎或者将数据另存为新表

```bash
flow data writer -c ${conf_path}
```

注: conf_path为参数路径，具体参数如下

**选项** 

| 参数名      | 必选 | 类型   | 说明           |
| :---------- | :--- | :----- | -------------- |
| table_name  | 是   | string | fate表名       |
| namespace   | 是   | int    | fate表命名空间 |
| storage_engine  | 否   | string    | 存储类型,如：MYSQL |
| address   | 否   | object    | 存储地址 |
| output_namespace   | 否   | string    | 另存为fate的表命名空间 |
| output_name   | 否   | string    | 另存为fate的表名 |
**注: storage_engine、address是组合参数，提供存储到指定引擎的功能；
output_namespace、output_name也是组合参数，提供另存为同种引擎的新表功能**

样例:

```json
{
  "table_name": "name1",
  "namespace": "namespace1",
  "output_name": "name2",
  "output_namespace": "namespace2"
}
```

**返回**

| 参数名  | 类型   | 说明     |
| :------ | :----- | -------- |
| jobId | string | 任务id |
| retcode | int    | 返回码   |
| retmsg  | string | 返回信息 |
| data    | object | 返回数据 |

样例

```json
{
    "data": {
        "board_url": "http://xxx.xxx.xxx.xxx:8080/index.html#/dashboard?job_id=202201121235115028490&role=local&party_id=0",
        "code": 0,
        "dsl_path": "/data/projects/fate/fateflow/jobs/202201121235115028490/job_dsl.json",
        "job_id": "202201121235115028490",
        "logs_directory": "/data/projects/fate/fateflow/logs/202201121235115028490",
        "message": "success",
        "model_info": {
            "model_id": "local-0#model",
            "model_version": "202201121235115028490"
        },
        "pipeline_dsl_path": "/data/projects/fate/fateflow/jobs/202201121235115028490/pipeline_dsl.json",
        "runtime_conf_on_party_path": "/data/projects/fate/fateflow/jobs/202201121235115028490/local/0/job_runtime_on_party_conf.json",
        "runtime_conf_path": "/data/projects/fate/fateflow/jobs/202201121235115028490/job_runtime_conf.json",
        "train_runtime_conf_path": "/data/projects/fate/fateflow/jobs/202201121235115028490/train_runtime_conf.json"
    },
    "jobId": "202201121235115028490",
    "retcode": 0,
    "retmsg": "success"
}
```
