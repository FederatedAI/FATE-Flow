## Resource

### query

For querying fate system resources

```bash
flow resource query
```

**Options** 

**Returns**

| parameter name | type | description |
| :------ | :----- | -------- |
| retcode | int | return code |
| retmsg | string | return message |
| data | object | return data |

**Example**

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

Resources for returning a job

```bash
flow resource return [options]
```

**Options** 

| parameter name | required | type | description |
| :----- | :--- | :----- | ------ |
| job_id | yes | string | job_id |

**Returns**

| parameter name | type | description |
| :------ | :----- | -------- |
| retcode | int | return code |
| retmsg | string | return message |
| data | object | return data |

**Example**

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
