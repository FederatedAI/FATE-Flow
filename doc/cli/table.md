## Table

### info

Query information about the fate table (real storage address, number, schema, etc.)

```bash
flow table info [options]
```

**options** 

| parameters    | short-format  | long-format | required  | type   | description    |
| :-------- | :--- | :--- | :--- | :----- | -------------- |
| table_name | `-t`   |`--table-name`   |yes   | string | fate table name     |
| namespace | `-n`   |`--namespace`   | yes |string   | fate table namespace |

**returns**
| parameter name | type | description |
| :------ | :----- | -------- |
| retcode | int | return code |
| retmsg | string | return information |
| data | object | return data |

Sample

```json
{
    "data": {
        "address": {
            "home": null,
            "name": "breast_hetero_guest",
            "namespace": "experiment"
        },
        "count": 569,
        "exists": 1,
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

You can delete table data with table delete

```bash
flow table delete [options]
```

**Options** 

| parameters    | short-format  | long-format | required  | type   | description    |
| :-------- | :--- | :--- | :--- | :----- | -------------- |
| table_name | `-t`   |`--table-name`   |yes   | string | fate table name     |
| namespace | `-n`   |`--namespace`   | yes |string   | fate table namespace |

**returns**

| parameter name | type | description |
| :------ | :----- | -------- |
| retcode | int | return code |
| retmsg | string | return message |
| data | object | return data |

Sample

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

Real storage addresses can be mapped to fate storage tables via table bind

```bash
flow table bind [options]
```

**options** 

| parameters | short format | long format | required | type | description |
| :-------- | :--- | :--- | :--- | :----- | -------------- |
| conf_path | `-c` | `--conf-path` | yes | string | configuration-path |

Note: conf_path is the parameter path, the specific parameters are as follows

| parameter_name | required | type | description |
| :------------- | :--- | :----- | ------------------------------------- |
| name | yes | string | fate table name |
| namespace | yes | string | fate table namespace |
| engine | yes | string | storage engine, supports "HDFS", "MYSQL", "PATH" |
| yes | object | real storage address |
| drop | no | int | Overwrite previous information |
| head | no | int | Whether there is a data table header |
| id_delimiter | no | string | Data separator |
| id_column | no | string | id field |
| feature_column | no | array | feature_field |

**mete information**

| parameter name | required | type | description |
|:---------------------|:----|:-------|-------------------------------------------|
| input_format | no | string | The format of the data (danse, svmlight, tag:value), used to determine |
| delimiter | no | string | The data separator, default "," |
| tag_with_value | no | bool | Valid for tag data format, whether to carry value |
| tag_value_delimiter | no | string | tag:value data separator, default ":" |
| with_match_id | no | bool | Whether or not to carry match id |
| with_match_id | no | object | The name of the id column, effective when extend_sid is enabled, e.g., ["email", "phone"] |
| id_range | no | object | For tag/svmlight format data, which columns are ids |
| exclusive_data_type | no | string | The format of the special type data columns |
| data_type | no | string | Column data type, default "float64 |
| with_label | no | bool | Whether to have a label, default False |
| label_name | no | string | The name of the label, default "y" |
| label_type | no | string | Label type, default "int" |

**In version 1.9.0 and later, if the meta parameter is passed in during the table bind phase, no anonymous information about the feature is generated directly. 
The feature anonymization information of the original data will be updated after the data has passed through the reader component once**

**Sample** 

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
**return**

| parameter name | type | description |
| :------ | :----- | -------- |
| retcode | int | return code |
| retmsg | string | return information |
| data | object | return data |

Sample

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

Tables can be made unavailable by table disable

```bash
flow table disable [options]
```

**Options** 

| parameters | short-format | long-format | required | type | description |
| :-------- | :--- | :--- | :--- | :----- | -------------- |
| table_name | `-t` | `--table-name` | yes | string | fate table name |
| namespace | `-n` |`--namespace` | yes |string | fate table namespace |

**returns**

| parameter name | type | description |
| :------ | :----- | -------- |
| retcode | int | return code |
| retmsg | string | return information |
| data | object | return data |

Sample

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

Tables can be made available with table enable

```bash
flow table enable [options]
```

**Options** 

| parameters | short-format | long-format | required | type | description |
| :-------- | :--- | :--- | :--- | :----- | -------------- |
| table_name | `-t` | `--table-name` | yes | string | fate table name |
| namespace | `-n` |`--namespace` | yes |string | fate table namespace |


**returns**

| parameter name | type | description |
| :------ | :----- | -------- |
| retcode | int | return code |
| retmsg | string | return information |
| data | object | return data |

Sample

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

Tables that are currently unavailable can be deleted with disable-delete

```bash
flow table disable-delete 
```


**return**

| parameter name | type | description |
| :------ | :----- | -------- |
| retcode | int | return-code |
| retmsg | string | return information |
| data | object | return data |

Sample

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


    