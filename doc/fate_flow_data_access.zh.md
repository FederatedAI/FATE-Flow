# FATE Flow 数据接入

[TOC]

## 1. 说明

- fate的存储表是由table name和namespace标识。

- fate提供upload组件供用户上传数据至fate计算引擎所支持的存储系统内；

- 若用户的数据已经存在于fate所支持的存储系统，可通过table bind方式将存储信息映射到fate存储表；

- 若table bind的表存储类型与当前默认引擎不一致，reader组件会自动转化存储类型;

  

## 2.  数据上传

**简要描述：** 

- 用于上传建模任务的输入数据到fate所支持的存储系统

**请求CLI** 

- `flow data upload -c $conf_path`

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




## 3.  表绑定
**简要描述：** 

- 可通过table bind将真实存储地址映射到fate存储表

**请求CLI** 
- `flow table bind -c $conf_path`

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




**返回参数** 

| 参数名  | 类型   | 说明     |
| :------ | :----- | -------- |
| retcode | int    | 返回码   |
| retmsg  | string | 返回信息 |
| data    | object | 返回数据 |

**样例** 

```json
{
    "data": {
        "namespace": "experiment",
        "table_name": "breast_hetero_guest"
    },
    "retcode": 0,
    "retmsg": "success"
}

```



## 4. 表信息查询

**简要描述：** 

- 用于查询fate表的相关信息(真实存储地址,数量,schema等)

**请求CLI** 

- `flow table info -t $name -n $namespace`

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

## 5. 删除表数据

### `delete`

**简要描述：** 
- 可通过table delete删除表数据

**请求CLI** 
- `flow table delete -t $name -n $namespace`

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



## 6.  数据下载

**简要描述：** 

- 用于下载fate存储引擎内的数据到文件格式数据

**请求CLI** 

- `flow data download -c $conf_path`

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



## 7.  reader组件

**简要描述：** 

- reader组件为fate的数据输入组件;
- reader组件可将输入数据转化为指定存储类型数据;

**参数配置**:

submit job时的conf中配置reader的输入表:

```shell
{
  "role": {
    "guest": {
      "0": {"reader_0": {"table": {"name": "breast_hetero_guest", "namespace": "experiment"}
    }
  }
}

```

**组件输出**

组件的输出数据存储引擎是由配置决定，配置文件conf/service_conf.yaml,配置项为:

```yaml
default_engines:
  storage: eggroll
```

- 计算引擎和存储引擎之间具有一定的支持依赖关系，依赖列表如下：

  | computing_engine | storage_engine                |
  | :--------------- | :---------------------------- |
  | standalone       | standalone                    |
  | eggroll          | eggroll                       |
  | spark            | hdfs(分布式), localfs(单机版) |

- reader组件输入数据的存储类型支持: eggroll、hdfs、localfs、mysql、path等;
- reader组件的输出数据类型由default_engines.storage配置决定(path除外)

