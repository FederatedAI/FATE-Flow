## Resource

### query

用于查询fate系统资源

```bash
flow resource query
```

**选项**

**返回**

| 参数名  | 类型   | 说明     |
| :------ | :----- | -------- |
| retcode | int    | 返回码   |
| retmsg  | string | 返回信息 |
| data    | object | 返回数据 |

**样例**

```json
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

**选项**

| 参数名 | 必选 | 类型   | 说明   |
| :----- | :--- | :----- | ------ |
| job_id | 是   | string | 任务id |

**返回**

| 参数名  | 类型   | 说明     |
| :------ | :----- | -------- |
| retcode | int    | 返回码   |
| retmsg  | string | 返回信息 |
| data    | object | 返回数据 |

**样例**

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
