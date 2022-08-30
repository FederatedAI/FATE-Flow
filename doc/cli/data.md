## Data

### upload

Used to upload the input data for the modeling task to the storage system supported by fate

```bash
flow data upload -c ${conf_path}
```

Note: conf_path is the parameter path, the specific parameters are as follows

**Options**

| parameter name | required | type | description                                                                                                                      |
| :------------------ | :--- | :----------- |----------------------------------------------------------------------------------------------------------------------------------|
| file | yes | string | data storage path                                                                                                                |
| id_delimiter | yes | string | Data separator, e.g. ","                                                                                                         |
| head | no | int | Whether the data has a table header                                                                                              | yes | int
| partition | yes | int | Number of data partitions                                                                                                        |
| storage_engine | no | string | storage engine type, default "EGGROLL", also support "HDFS", "LOCALFS", "HIVE", etc.                                             |
| namespace | yes | string | table namespace                                                                                                                  | yes
| table_name | yes | string | table name                                                                                                                       |
| storage_address | no | object | The storage address of the corresponding storage engine is required                                                              
| use_local_data | no | int | The default is 1, which means use the data from the client's machine; 0 means use the data from the fate flow service's machine. 
| drop | no | int | Whether to overwrite uploads                                                                                                     |
| extend_sid | no | bool | Whether to add a new column for uuid id, default False                                                                           |
| auto_increasing_sid | no | bool | Whether the new id column is self-increasing (will only work if extend_sid is True), default False                               |

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

**In version 1.9.0 and later, passing in the meta parameter will generate anonymous information about the feature.**
**Example** 

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

**return parameters** 

| parameter name | type | description |
| :------ | :----- | -------- |
| jobId | string | job id |
| retcode | int | return code |
| retmsg | string | return message |
| data | object | return data |

**Example** 

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
        "runtime_conf_path":"/data/projects/fate/jobs/202111081218319075660/job_runtime_conf.json",
        "table_name": "breast_hetero_host",
        "train_runtime_conf_path":"/data/projects/fate/jobs/202111081218319075660/train_runtime_conf.json"
    },
    "jobId": "202111081218319075660",
    "retcode": 0,
    "retmsg": "success"
}

```

### upload-history

Used to query upload table history.

```
flow data upload-history -l 20
flow data upload-history --job-id $JOB_ID
```

**Options**

| parameter name | required | type   | description                                |
| :------------- | :------- | :----- | ------------------------------------------ |
| -l --limit     | no       | int    | Number of records to return. (default: 10) |
| -j --job_id    | no       | string | Job ID                                     |
|                |          |        |                                            |

### download

**Brief description:** 

Used to download data from within the fate storage engine to file format data

```bash
flow data download -c ${conf_path}
```

Note: conf_path is the parameter path, the specific parameters are as follows

**Options**

| parameter name | required | type | description |
| :---------- | :--- | :----- | -------------- |
| output_path | yes | string | download_path |
| table_name | yes | string | fate table name |
| namespace | yes | int | fate table namespace |

Example:

```json
{
  "output_path": "/data/projects/fate/breast_hetero_guest.csv",
  "namespace": "experiment",
  "table_name": "breast_hetero_guest"
}
```

**return parameters** 

| parameter name | type | description |
| :------ | :----- | -------- |
| jobId | string | job id |
| retcode | int | return code |
| retmsg | string | return message |
| data | object | return data |

**Example** 

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

**Brief description:** 

Used to download data from the fate storage engine to the external engine or to save data as a new table

```bash
flow data writer -c ${conf_path}
```

Note: conf_path is the parameter path, the specific parameters are as follows

**Options** 

| parameter name | required | type | description |
| :---------- | :--- | :----- | -------------- |
| table_name | yes | string | fate table name |
| namespace | yes | int | fate table namespace |
| storage_engine | no | string | Storage type, e.g., MYSQL |
| address | no | object | storage_address |
| output_namespace | no | string | Save as a table namespace for fate |
| output_name | no | string | Save as fate's table name |
**Note: storage_engine, address are combined parameters that provide storage to the specified engine.
output_namespace, output_name are also combined parameters, providing the function to save as a new table of the same engine**

Example:

```json
{
  "table_name": "name1",
  "namespace": "namespace1",
  "output_name": "name2",
  "output_namespace": "namespace2"
}
```

**return**

| parameter name | type | description |
| :------ | :----- | -------- |
| jobId | string | job id |
| retcode | int | return code |
| retmsg | string | return information |
| data | object | return data |

**Example** 

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
        "runtime_conf_path":"/data/projects/fate/fateflow/jobs/202201121235115028490/job_runtime_conf.json",
        "train_runtime_conf_path": "/data/projects/fate/fateflow/jobs/202201121235115028490/train_runtime_conf.json"
    },
    "jobId": "202201121235115028490",
    "retcode": 0,
    "retmsg": "success"
}
```
