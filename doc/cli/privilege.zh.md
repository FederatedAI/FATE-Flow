## Privilege

### grant

添加权限

```bash
flow privilege grant -c fateflow/examples/permission/grant.json
```

**选项**

| 参数    | 短格式 | 长格式 | 必选 | 类型   | 说明           |
| :-------- | :--- | :--- | :--- | :----- | -------------- |
| conf_path | `-c`   |`--conf-path`   |是   | string | 配置路径  |

注: conf_path为参数路径，具体参数如下

| 参数名       | 必选  | 类型     | 说明       |
|:----------|:----|:-------|----------|
| party_id  | 是   | string | 站点id     |
| component | 否   | string | 组件名，可用","分割多个组件，"*"为所有组件 |
| dataset   | 否   | object | 数据集列表    |


**样例**
```json
{
  "party_id": 10000,
  "component": "reader,dataio",
  "dataset": [
    {
      "namespace": "experiment",
      "name": "breast_hetero_guest"
    },
    {
      "namespace": "experiment",
      "name": "breast_hetero_host"
    }
  ]
}
```

**返回**

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
flow privilege delete -c fateflow/examples/permission/delete.json
```
**选项**

| 参数    | 短格式 | 长格式 | 必选 | 类型   | 说明           |
| :-------- | :--- | :--- | :--- | :----- | -------------- |
| conf_path | `-c`   |`--conf-path`   |是   | string | 配置路径  |


注: conf_path为参数路径，具体参数如下

| 参数名       | 必选  | 类型     | 说明                       |
|:----------|:----|:-------|--------------------------|
| party_id  | 是   | string | 站点id                     |
| component | 否   | string | 组件名，可用","分割多个组件，"*"为所有组件 |
| dataset   | 否   | object | 数据集列表， "*"为所有数据集         |

**样例**
```json
{
  "party_id": 10000,
  "component": "reader,dataio",
  "dataset": [
    {
      "namespace": "experiment",
      "name": "breast_hetero_guest"
    },
    {
      "namespace": "experiment",
      "name": "breast_hetero_host"
    }
  ]
}
```

**返回**

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
flow privilege query -p 10000
```

**选项**

| 参数    | 短格式  | 长格式          | 必选 | 类型   | 说明   |
| :-------- |:-----|:-------------| :--- | :----- |------|
| party_id | `-p` | `--party-id` |是   | string | 站点id |

**返回**


| 参数名  | 类型   | 说明     |
| ------- | :----- | -------- |
| retcode | int    | 返回码   |
| retmsg  | string | 返回信息 |
| data    | object | 返回数据 |

**样例**

```json
{
    "data": {
        "component": [
            "reader",
            "dataio"
        ],
        "dataset": [
            {
                "name": "breast_hetero_guest",
                "namespace": "experiment"
            },
            {
                "name": "breast_hetero_host",
                "namespace": "experiment"
            }
        ]
    },
    "retcode": 0,
    "retmsg": "success"
}

```
