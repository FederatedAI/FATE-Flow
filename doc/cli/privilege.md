## Privilege

### grant

Add privileges

```bash
flow privilege grant -c fateflow/examples/permission/grant.json
```

**Options**

| parameter name | required | type | description                                                                         |
|:----------|:----|:-------|-------------------------------------------------------------------------------------|
| party_id | yes | string | site id                                                                             |
| component | no | string | component name, can be split by "," for multiple components, "*" for all components |
| dataset | no | object | list of datasets                                                                    |


**sample**
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

**return**

| parameter name | type | description |
| ------- | :----- | -------- |
| retcode | int | return code |
| retmsg | string | return message |

**Sample**

```shell
{
    "retcode": 0,
    "retmsg": "success"
}
```

### delete

Delete permissions

```bash
flow privilege delete -c fateflow/examples/permission/delete.json
```
**Options**

| parameter name | required | type | description |
|:----------|:----|:-------|--------------------------|
| party_id | yes | string | site_id |
| component | no | string | component name, can be split by "," for multiple components, "*" for all components |
| dataset | no | object | list of datasets, "*" is all datasets |

**sample**
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

**return**

| parameter name | type | description |
| ------- | :----- | -------- |
| retcode | int | return code |
| retmsg | string | return message |

**Sample**

```shell
{
    "retcode": 0,
    "retmsg": "success"
}
```

### query

Query permissions

```bash
flow privilege query -p 10000
```

**Options**

| parameters | short-format | long-format | required | type | description |
| :-------- |:-----|:-------------| :--- | :----- |------|
| party_id | `-p` | `--party-id` | yes | string | site id |

**returns**


| parameter name | type | description |
| ------- | :----- | -------- |
| retcode | int | return-code |
| retmsg | string | Return information |
| data | object | return data |

**Sample**

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