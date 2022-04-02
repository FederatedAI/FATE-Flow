## Table

### info

用于查询fate表的相关信息(真实存储地址,数量,schema等)

```bash
flow table info [options]
```

**选项** 

| 参数    | 短格式 | 长格式 | 必选 | 类型   | 说明           |
| :-------- | :--- | :--- | :--- | :----- | -------------- |
| table_name | `-t`   |`--table-name`   |是   | string | fate表名       |
| namespace | `-n`   |`--namespace`   | 是 |string   | fate表命名空间 |

**返回**

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

**选项** 

| 参数    | 短格式 | 长格式 | 必选 | 类型   | 说明           |
| :-------- | :--- | :--- | :--- | :----- | -------------- |
| table_name | `-t`   |`--table-name`   |是   | string | fate表名       |
| namespace | `-n`   |`--namespace`   | 是 |string   | fate表命名空间 |

**返回**

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

**选项** 

| 参数    | 短格式 | 长格式 | 必选 | 类型   | 说明           |
| :-------- | :--- | :--- | :--- | :----- | -------------- |
| conf_path | `-c`   |`--conf-path`   |是   | string | 配置路径  |

注: conf_path为参数路径，具体参数如下

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
**返回**

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


### disable

可通过table disable将表置为不可用状态

```bash
flow table disable [options]
```

**选项** 

| 参数    | 短格式 | 长格式 | 必选 | 类型   | 说明           |
| :-------- | :--- | :--- | :--- | :----- | -------------- |
| table_name | `-t`   |`--table-name`   |是   | string | fate表名       |
| namespace | `-n`   |`--namespace`   | 是 |string   | fate表命名空间 |

**返回**

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

### enable

可通过table enable将表置为可用状态

```bash
flow table enable [options]
```

**选项** 

| 参数    | 短格式 | 长格式 | 必选 | 类型   | 说明           |
| :-------- | :--- | :--- | :--- | :----- | -------------- |
| table_name | `-t`   |`--table-name`   |是   | string | fate表名       |
| namespace | `-n`   |`--namespace`   | 是 |string   | fate表命名空间 |


**返回**

| 参数名  | 类型   | 说明     |
| :------ | :----- | -------- |
| retcode | int    | 返回码   |
| retmsg  | string | 返回信息 |
| data    | object | 返回数据 |

样例

```json
{
    "data": [{
        "namespace": "xxx",
        "table_name": "xxx"
    }],
    "retcode": 0,
    "retmsg": "success"
}
```

### disable-delete

可通过disable-delete删除当前不可用的表

```bash
flow table disable-delete 
```


**返回**

| 参数名  | 类型   | 说明     |
| :------ | :----- | -------- |
| retcode | int    | 返回码   |
| retmsg  | string | 返回信息 |
| data    | object | 返回数据 |

样例

```json
{
  "data": [
    {
      "namespace": "xxx",
      "table_name": "xxx"
    },
    {
      "namespace": "xxx",
      "table_name": "xxx"
    }
  ],
  "retcode": 0,
  "retmsg": "success"
}
```