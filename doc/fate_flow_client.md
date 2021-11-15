# FATE Flow Client

[TOC]

## 1. Instructions

- Introduces how to install and use the `FATE Flow Client`, which is usually included in the `FATE Client`, which contains several clients of the `FATE Project`: `Pipeline` `FATE Flow Client` `FATE Test`
- Introducing the command line provided by `FATE Flow Client`, all commands will have a common invocation portal, you can type `flow` in the command line to get all the command categories and their subcommands

```bash
    [IN]
    flow

    [OUT]
    Usage： flow [OPTIONS] COMMAND [ARGS]...

      Fate Flow Client

    Options：
      -h, --help  Show this message and exit.

    Commands：
      component   Component Operations
      data        Data Operations
      init        Flow CLI Init Command
      job         Job Operations
      model       Model Operations
      queue       Queue Operations
      table       Table Operations
      task        Task Operations
```

For more information, please consult the following documentation or use the `flow --help` command.

## 2. Installation of FATE Client

### 2.1 Online installation

FATE Client will be distributed to `pypi`, you can use `pip` and other tools to install the corresponding version directly, such as

```bash
pip install fatale-client
```

or

```bash
pip install atmosphere-client==${version}
```

### 2.2 Installing on a FATE cluster

Please install on a machine with version 1.5.1 and above of FATE.

Installation command.

```shell
cd $FATE_PROJECT_BASE/
# Enter the virtual environment of FATE PYTHON
source bin/init_env.sh
# Execute the installation
cd . /fate/python/fate_client && python setup.py install
```

Once the installation is complete, type `flow` on the command line and enter, the installation will be considered successful if you get the following return.

```shell
Usage: flow [OPTIONS] COMMAND [ARGS]...

  Fate Flow Client

Options:
  -h, --help Show this message and exit.

Commands:
  component Component Operations
  data Data Operations
  init Flow CLI Init Command
  Job Job Operations
  model Model Operations
  queue Queue Operations
  Table Table Operations
  tag Tag Operations
  task Task Operations
```

## 3. initialization

Before using fate-client, you need to initialize it. It is recommended to use the configuration file of fateflow to initialize it.

### 3.1 Specify the fateflow service address

```bash
# Specify the IP address and port of the fateflow service for initialization
flow init --ip 192.168.0.1 --port 9380
```

### 3.2 Pass the configuration file on the FATE cluster

```shell
# Go to the FATE installation path, e.g. /data/projects/fate
cd $FATE_PROJECT_BASE/
flow init -c . /conf/service_conf.yaml
```

The initialization is considered successful if you get the following return.

```json
{
    "retcode": 0,
    "retmsg": "Fate Flow CLI has been initialized successfully."
}
```

## 4. Verification

Verify that the client can connect to the `FATE Flow Server`, e.g. try to query the current job status

```bash
flow job query
```

Usually the `retcode` in the return is just `0`

```json
{
    "data": [],
    "retcode": 0,
    "retmsg": "no job could be found"
}
```

If the return is similar to the following, it means that the connection is not available, please check the network condition

```json
{
    "retcode": 100,
    "retmsg": "Connection refused. Please check if the fate flow service is started"
}
```

## 5. Data

### `upload`

-   *Description*: Upload Data Table.
-   *Arguments*:

| No. | Argument  | Flag_1 | Flag_2        | Required | Description                                                                                                                                    |
| --- | --------- | ------ | ------------- | -------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | conf_path | `-c`   | `--conf-path` | Yes      | Configuration file path                                                                                                                        |
| 2   | verbose   |        | `--verbose`   | No       | If specified, verbose mode will be turn on. Users can have feedback on upload task in progress. (Default: False)                               |
| 3   | drop      |        | `--drop`      | No       | If specified, data of old version would be replaced by the current version. Otherwise, current upload task would be rejected. (Default: False) |

-   *Examples*:

``` bash
flow data upload -c fate_flow/examples/upload_guest.json
flow data upload -c fate_flow/examples/upload_host.json --verbose --drop
```

### `download`

-   *Description*: Download Data Table.
-   *Arguments*:

| No. | Argument  | Flag_1 | Flag_2        | Required | Description             |
| --- | --------- | ------ | ------------- | -------- | ----------------------- |
| 1   | conf_path | `-c`   | `--conf-path` | Yes      | Configuration file path |

-   *Examples*:

``` bash
flow data download -c fate_flow/examples/download_host.json
```

### `upload-history`

-   *Description*: Query Upload Table History.
-   *Arguments*:

| No. | Argument | Flag_1 | Flag_2     | Required | Description                                |
| --- | -------- | ------ | ---------- | -------- | ------------------------------------------ |
| 1   | limit    | `-l`   | `--limit`  | No       | Number of records to return. (default: 10) |
| 2   | job_id   | `-j`   | `--job_id` | No       | Job ID                                     |

-   *Examples*:

``` bash
flow data upload-history -l 20
flow data upload-history --job-id $JOB_ID
```

## 6. Job

### `submit`

-   *Description*: Submit a pipeline job.
-   *Arguments*:

| No. | Argument  | Flag_1 | Flag_2        | Required | Description                                                                                                                                                                                              |
| --- | --------- | ------ | ------------- | -------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | conf_path | `-c`   | `--conf-path` | Yes      | Runtime configuration file path                                                                                                                                                                          |
| 2   | dsl_path  | `-d`   | `--dsl-path`  | Yes      | Domain-specific language(DSL) file path. If the type of job is 'predict', you can leave this feature blank, or you can provide a valid dsl file to replace the one that aotumatically generated by fate. |

-   *Examples*:

``` bash
flow job submit -c fate_flow/examples/test_hetero_lr_job_conf.json -d fate_flow/examples/test_hetero_lr_job_dsl.json
```

### `stop`

-   *Description*: Cancel or stop a specified job.
-   *Arguments*:

| No. | Argument | Flag_1 | Flag_2     | Required | Description     |
| --- | -------- | ------ | ---------- | -------- | --------------- |
| 1   | job_id   | `-j`   | `--job_id` | Yes      | A valid job id. |

-   *Examples*:

    ``` bash
    flow job stop -j $JOB_ID
    ```

### `query`

-   *Description*: Query job information by filters.
-   *Arguments*:

| No. | Argument | Flag_1 | Flag_2       | Required | Description     |
| --- | -------- | ------ | ------------ | -------- | --------------- |
| 1   | job_id   | `-j`   | `--job_id`   | No       | A valid job id. |
| 2   | role     | `-r`   | `--role`     | No       | Role            |
| 3   | party_id | `-p`   | `--party_id` | No       | Party ID        |
| 4   | status   | `-s`   | `--status`   | No       | Job Status      |

-   *Examples*:

    ``` bash
    flow job query -r guest -p 9999 -s complete
    flow job query -j $JOB_ID
    ```

### `view`

-   *Description*: Query data view information by filters.
-   *Arguments*:

| No. | Argument | Flag_1 | Flag_2       | Required | Description     |
| --- | -------- | ------ | ------------ | -------- | --------------- |
| 1   | job_id   | `-j`   | `--job_id`   | Yes      | A valid job id. |
| 2   | role     | `-r`   | `--role`     | Yes      | Role            |
| 3   | party_id | `-p`   | `--party_id` | Yes      | Party ID        |
| 4   | status   | `-s`   | `--status`   | Yes      | Job Status      |

-   *Examples*:

    ``` bash
    flow job view -j $JOB_ID -s complete
    ```

### `config`

-   *Description*: Download the configuration of a specified job.
-   *Arguments*:

| No. | Argument    | Flag_1 | Flag_2          | Required | Description     |
| --- | ----------- | ------ | --------------- | -------- | --------------- |
| 1   | job_id      | `-j`   | `--job_id`      | Yes      | A valid job id. |
| 2   | role        | `-r`   | `--role`        | Yes      | Role            |
| 3   | party_id    | `-p`   | `--party_id`    | Yes      | Party ID        |
| 4   | output_path | `-o`   | `--output-path` | Yes      | Output Path     |

-   *Examples*：

    ``` bash
    flow job config -j $JOB_ID -r host -p 10000 --output-path ./examples/
    ```

### `log`

-   *Description*: Download log files of a specified job.
-   *Arguments*:

| No. | Argument    | Flag_1 | Flag_2          | Required | Description     |
| --- | ----------- | ------ | --------------- | -------- | --------------- |
| 1   | job_id      | `-j`   | `--job_id`      | Yes      | A valid job id. |
| 2   | output_path | `-o`   | `--output-path` | Yes      | Output Path     |

-   *Examples*:

    ``` bash
    flow job log -j JOB_ID --output-path ./examples/
    ```

### `list`

-   *Description*: List jobs.
-   *Arguments*:

| No. | Argument | Flag_1 | Flag_2    | Required | Description                                |
| --- | -------- | ------ | --------- | -------- | ------------------------------------------ |
| 1   | limit    | `-l`   | `--limit` | No       | Number of records to return. (default: 10) |

-   *Examples*:

``` bash
flow job list
flow job list -l 30
```

### `dsl`

-   *Description*: A predict dsl generator.
-   *Arguments*:

| No. | Argument       | Flag_1 | Flag_2             | Required | Description                                                  |
| --- | -------------- | ------ | ------------------ | -------- | ------------------------------------------------------------ |
| 1   | cpn_list       |        | `--cpn-list`       | No       | User inputs a string to specify component list.              |
| 2   | cpn_path       |        | `--cpn-path`       | No       | User specifies a file path which records the component list. |
| 3   | train_dsl_path |        | `--train-dsl-path` | Yes      | User specifies the train dsl file path.                      |
| 4   | output_path    | `-o`   | `--output-path`    | No       | User specifies output directory path.                        |

-   *Examples*:

``` bash
flow job dsl --cpn-path fate_flow/examples/component_list.txt --train-dsl-path fate_flow/examples/test_hetero_lr_job_dsl.json

flow job dsl --cpn-path fate_flow/examples/component_list.txt --train-dsl-path fate_flow/examples/test_hetero_lr_job_dsl.json -o fate_flow/examples/

flow job dsl --cpn-list "dataio_0, hetero_feature_binning_0, hetero_feature_selection_0, evaluation_0" --train-dsl-path fate_flow/examples/test_hetero_lr_job_dsl.json -o fate_flow/examples/

flow job dsl --cpn-list [dataio_0,hetero_feature_binning_0,hetero_feature_selection_0,evaluation_0] --train-dsl-path fate_flow/examples/test_hetero_lr_job_dsl.json -o fate_flow/examples/
```

## 7. TRACKING

### `parameters`

-   *Description*: Query the arguments of a specified component.
-   *Arguments*:

| No. | Argument       | Flag_1 | Flag_2             | Required | Description     |
| --- | -------------- | ------ | ------------------ | -------- | --------------- |
| 1   | job_id         | `-j`   | `--job_id`         | Yes      | A valid job id. |
| 2   | role           | `-r`   | `--role`           | Yes      | Role            |
| 3   | party_id       | `-p`   | `--party_id`       | Yes      | Party ID        |
| 4   | component_name | `-cpn` | `--component_name` | Yes      | Component Name  |

-   *Examples*:

``` bash
flow component parameters -j $JOB_ID -r host -p 10000 -cpn hetero_feature_binning_0
```

### `metric-all`

-   *Description*: Query all metric data.
-   *Arguments*:

| No. | Argument       | Flag_1 | Flag_2             | Required | Description     |
| --- | -------------- | ------ | ------------------ | -------- | --------------- |
| 1   | job_id         | `-j`   | `--job_id`         | Yes      | A valid job id. |
| 2   | role           | `-r`   | `--role`           | Yes      | Role            |
| 3   | party_id       | `-p`   | `--party_id`       | Yes      | Party ID        |
| 4   | component_name | `-cpn` | `--component_name` | Yes      | Component Name  |

-   *Examples*:

    ``` bash
    flow component metric-all -j $JOB_ID -r host -p 10000 -cpn hetero_feature_binning_0
    ```

### `metrics`

-   *Description*: Query the list of metrics.
-   *Arguments*:

| No. | Argument       | Flag_1 | Flag_2             | Required | Description     |
| --- | -------------- | ------ | ------------------ | -------- | --------------- |
| 1   | job_id         | `-j`   | `--job_id`         | Yes      | A valid job id. |
| 2   | role           | `-r`   | `--role`           | Yes      | Role            |
| 3   | party_id       | `-p`   | `--party_id`       | Yes      | Party ID        |
| 4   | component_name | `-cpn` | `--component_name` | Yes      | Component Name  |

-   *Examples*:

    ``` bash
    flow component metrics -j $JOB_ID -r host -p 10000 -cpn hetero_feature_binning_0
    ```

### `metric-delete`

-   *Description*: Delete specified metric.
-   *Arguments*:

| No. | Argument | Flag_1 | Flag_2     | Required | Description                                   |
| --- | -------- | ------ | ---------- | -------- | --------------------------------------------- |
| 1   | date     | `-d`   | `--date`   | No       | An 8-Digit Valid Date, Format Like 'YYYYMMDD' |
| 2   | job_id   | `-j`   | `--job_id` | No       | Job ID                                        |

-   *Examples*:

``` bash
# NOTICE: If you input both two optional arguments, the 'date' argument will be detected in priority while the 'job_id' argument would be ignored.
flow component metric-delete -d 20200101
flow component metric-delete -j $JOB_ID
```

### `output-model`

-   *Description*: Query a specified component model.
-   *Arguments*:

| No. | Argument       | Flag_1 | Flag_2             | Required | Description    |
| --- | -------------- | ------ | ------------------ | -------- | -------------- |
| 1   | job_id         | `-j`   | `--job_id`         | Yes      | Job ID         |
| 2   | role           | `-r`   | `--role`           | Yes      | Role           |
| 3   | party_id       | `-p`   | `--party_id`       | Yes      | Party ID       |
| 4   | component_name | `-cpn` | `--component_name` | Yes      | Component Name |

-   *Examples*:

    ``` bash
    flow component output-model -j $JOB_ID -r host -p 10000 -cpn hetero_feature_binning_0
    ```

### `output-data`

-   *Description*: Download the output data of a specified component.
-   *Arguments*:

| No. | Argument       | Flag_1 | Flag_2             | Required | Description                                                   |
| --- | -------------- | ------ | ------------------ | -------- | ------------------------------------------------------------- |
| 1   | job_id         | `-j`   | `--job_id`         | Yes      | Job ID                                                        |
| 2   | role           | `-r`   | `--role`           | Yes      | Role                                                          |
| 3   | party_id       | `-p`   | `--party_id`       | Yes      | Party ID                                                      |
| 4   | component_name | `-cpn` | `--component_name` | Yes      | Component Name                                                |
| 5   | output_path    | `-o`   | `--output-path`    | Yes      | User specifies output directory path                          |
| 6   | limit          | `-l`   | `--limit`          | No       | Number of records to return, default -1 means return all data |

-   *Examples*:

    ``` bash
    flow component output-data -j $JOB_ID -r host -p 10000 -cpn hetero_feature_binning_0 --output-path ./examples/
    ```

### `output-data-table`

-   *Description*: View table name and namespace.
-   *Arguments*:

| No. | Argument       | Flag_1 | Flag_2             | Required | Description    |
| --- | -------------- | ------ | ------------------ | -------- | -------------- |
| 1   | job_id         | `-j`   | `--job_id`         | Yes      | Job ID         |
| 2   | role           | `-r`   | `--role`           | Yes      | Role           |
| 3   | party_id       | `-p`   | `--party_id`       | Yes      | Party ID       |
| 4   | component_name | `-cpn` | `--component_name` | Yes      | Component Name |

-   *Examples*:

    ``` bash
    flow component output-data-table -j $JOB_ID -r host -p 10000 -cpn hetero_feature_binning_0
    ```

### `list`

-   *Description*: List components of a specified job.
-   *Arguments*:

| No. | Argument | Flag_1 | Flag_2     | Required | Description |
| --- | -------- | ------ | ---------- | -------- | ----------- |
| 1   | job_id   | `-j`   | `--job_id` | Yes      | Job ID      |

-   *Examples*:

``` bash
flow component list -j $JOB_ID
```

### `get-summary`

-   *Description*: Download summary of a specified component and save it
    as a json file.
-   *Arguments*:

| No. | Argument       | Flag_1 | Flag_2             | Required | Description                          |
| --- | -------------- | ------ | ------------------ | -------- | ------------------------------------ |
| 1   | job_id         | `-j`   | `--job_id`         | Yes      | Job ID                               |
| 2   | role           | `-r`   | `--role`           | Yes      | Role                                 |
| 3   | party_id       | `-p`   | `--party_id`       | Yes      | Party ID                             |
| 4   | component_name | `-cpn` | `--component_name` | Yes      | Component Name                       |
| 5   | output_path    | `-o`   | `--output-path`    | No       | User specifies output directory path |

-   *Examples*:

``` bash
flow component get-summary -j $JOB_ID -r host -p 10000 -cpn hetero_feature_binning_0

flow component get-summary -j $JOB_ID -r host -p 10000 -cpn hetero_feature_binning_0 -o ./examples/
```

## 8. Model

### `load`

-   *Description*: Load model. Need to deploy model first if <span
    class="title-ref">dsl_version</span> == <span
    class="title-ref">2</span>.
-   *Arguments*:

| No. | Argument  | Flag_1 | Flag_2        | Required | Description                     |
| --- | --------- | ------ | ------------- | -------- | ------------------------------- |
| 1   | conf_path | `-c`   | `--conf-path` | No       | Runtime configuration file path |
| 2   | job_id    | `-j`   | `--job_id`    | No       | Job ID                          |

-   *Examples*:

``` bash
flow model load -c fate_flow/examples/publish_load_model.json
flow model load -j $JOB_ID
```

### `bind`

-   *Description*: Bind model. Need to deploy model first if <span
    class="title-ref">dsl_version</span> == <span
    class="title-ref">2</span>.
-   *Arguments*:

| No. | Argument  | Flag_1 | Flag_2        | Required | Description                     |
| --- | --------- | ------ | ------------- | -------- | ------------------------------- |
| 1   | conf_path | `-c`   | `--conf-path` | Yes      | Runtime configuration file path |
| 2   | job_id    | `-j`   | `--job_id`    | No       | Job ID                          |

-   *Examples*:

``` bash
flow model bind -c fate_flow/examples/bind_model_service.json
flow model bind -c fate_flow/examples/bind_model_service.json -j $JOB_ID
```

### `import`

-   *Description*: Import model
-   *Arguments*:

| No. | Argument      | Flag_1 | Flag_2          | Required | Description                                                                                                                                  |
| --- | ------------- | ------ | --------------- | -------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | conf_path     | `-c`   | `--conf-path`   | Yes      | Runtime configuration file path                                                                                                              |
| 2   | from-database |        | --from-database | No       | If specified and there is a valid database environment, fate flow will import model from database which you specified in configuration file. |

-   *Examples*:

``` bash
flow model import -c fate_flow/examples/import_model.json
flow model import -c fate_flow/examples/restore_model.json --from-database
```

### `export`

-   *Description*: Export model
-   *Arguments*:

| No. | Argument    | Flag_1 | Flag_2          | Required | Description                                                                                                                                |
| --- | ----------- | ------ | --------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| 1   | conf_path   | `-c`   | `--conf-path`   | Yes      | Runtime configuration file path                                                                                                            |
| 2   | to-database |        | `--to-database` | No       | If specified and there is a valid database environment, fate flow will export model to database which you specified in configuration file. |

-   *Examples*:

``` bash
flow model export -c fate_flow/examples/export_model.json
flow model export -c fate_flow/examplse/store_model.json --to-database
```

### `migrate`

-   *Description*: Migrate model
-   *Arguments*:

| No. | Argument  | Flag_1 | Flag_2        | Required | Description                     |
| --- | --------- | ------ | ------------- | -------- | ------------------------------- |
| 1   | conf_path | `-c`   | `--conf-path` | Yes      | Runtime configuration file path |

-   *Examples*:

``` bash
flow model migrate -c fate_flow/examples/migrate_model.json
```

### `tag-list`

-   *Description*: List tags of model.
-   *Arguments*:

| No. | Argument | Flag_1 | Flag_2     | Required | Description |
| --- | -------- | ------ | ---------- | -------- | ----------- |
| 1   | job_id   | `-j`   | `--job_id` | Yes      | Job ID      |

-   *Examples*:

``` bash
flow model tag-list -j $JOB_ID
```

### `tag-model`

-   *Description*: Tag model.
-   *Arguments*:

| No. | Argument | Flag_1 | Flag_2       | Required | Description                                                                                          |
| --- | -------- | ------ | ------------ | -------- | ---------------------------------------------------------------------------------------------------- |
| 1   | job_id   | `-j`   | `--job_id`   | Yes      | Job ID                                                                                               |
| 2   | tag_name | `-t`   | `--tag-name` | Yes      | The name of tag                                                                                      |
| 3   | remove   |        | `--remove`   | No       | If specified, the name of specified model will be removed from the model name list of specified tag. |

-   *Examples*:

``` bash
flow model tag-model -j $JOB_ID -t $TAG_NAME
flow model tag-model -j $JOB_ID -t $TAG_NAME --remove
```

### `deploy`

-   *Description*: Deploy model.
-   *Arguments*:

| No. | Argument      | Flag_1 | Flag_2             | Required | Description                                                  |
| --- | ------------- | ------ | ------------------ | -------- | ------------------------------------------------------------ |
| 1   | model_id      |        | `--model-id`       | Yes      | Parent model id.                                             |
| 2   | model_version |        | `--model-version`  | Yes      | Parent model version.                                        |
| 3   | cpn_list      |        | `--cpn-list`       | No       | User inputs a string to specify component list.              |
| 4   | cpn_path      |        | `--cpn-path`       | No       | User specifies a file path which records the component list. |
| 5   | dsl_path      |        | `--train-dsl-path` | No       | User specified predict dsl file.                             |

-   *Examples*:

``` bash
flow model deploy --model-id $MODEL_ID --model-version $MODEL_VERSION
```

### `get-predict-dsl`

-   *Description*: Get predict dsl of model.
-   *Arguments*:

| No. | Argument      | Flag_1 | Flag_2            | Required | Description           |
| --- | ------------- | ------ | ----------------- | -------- | --------------------- |
| 1   | model_id      |        | `--model-id`      | Yes      | Model id              |
| 2   | model_version |        | `--model-version` | Yes      | Model version         |
| 3   | output_path   | `-o`   | `--output-path`   | Yes      | Output directory path |

-   *Examples*:

``` bash
flow model get-predict-dsl --model-id $MODEL_ID --model-version $MODEL_VERSION -o ./examples/
```

### `get-predict-conf`

-   *Description*: Get predict conf template of model.
-   *Arguments*:

| No. | Argument      | Flag_1 | Flag_2            | Required | Description           |
| --- | ------------- | ------ | ----------------- | -------- | --------------------- |
| 1   | model_id      |        | `--model-id`      | Yes      | Model id              |
| 2   | model_version |        | `--model-version` | Yes      | Model version         |
| 3   | output_path   | `-o`   | `--output-path`   | Yes      | Output directory path |

-   *Examples*:

``` bash
flow model get-predict-conf --model-id $MODEL_ID --model-version $MODEL_VERSION -o ./examples/
```

### `get-model-info`

-   *Description*: Get information of model.
-   *Arguments*:

| No. | Argument      | Flag_1 | Flag_2            | Required | Description   |
| --- | ------------- | ------ | ----------------- | -------- | ------------- |
| 1   | model_id      |        | `--model-id`      | No       | Model id      |
| 2   | model_version |        | `--model-version` | Yes      | Model version |
| 3   | role          | `-r`   | `--role`          | No       | Role          |
| 2   | party_id      | `-p`   | `--party-id`      | No       | Party ID      |
| 3   | detail        |        | `--detail`        | No       | Show details  |

-   *Examples*:

``` bash
flow model get-model-info --model-id $MODEL_ID --model-version $MODEL_VERSION
flow model get-model-info --model-id $MODEL_ID --model-version $MODEL_VERSION --detail
```

## 9. Table

### `info`

-   *Description*: Query Table Information.
-   *Arguments*:

| No. | Argument   | Flag_1 | Flag_2         | Required | Description |
| --- | ---------- | ------ | -------------- | -------- | ----------- |
| 1   | namespace  | `-n`   | `--namespace`  | Yes      | Namespace   |
| 2   | table_name | `-t`   | `--table-name` | Yes      | Table Name  |

-   *Examples*:

``` bash
flow table info -n $NAMESPACE -t $TABLE_NAME
```

### `delete`

-   *Description*: Delete A Specified Table.
-   *Arguments*:

| No. | Argument   | Flag_1 | Flag_2         | Required | Description |
| --- | ---------- | ------ | -------------- | -------- | ----------- |
| 1   | namespace  | `-n`   | `--namespace`  | No       | Namespace   |
| 2   | table_name | `-t`   | `--table_name` | No       | Table name  |

-   *Examples*:

``` bash
flow table delete -n $NAMESPACE -t $TABLE_NAME
```

## 10. Task

### `query`

-   *Description*: Query task information by filters.
-   *Arguments*:

| No. | Argument       | Flag_1 | Flag_2             | Required | Description    |
| --- | -------------- | ------ | ------------------ | -------- | -------------- |
| 1   | job_id         | `-j`   | `--job_id`         | No       | Job ID         |
| 2   | role           | `-r`   | `--role`           | No       | Role           |
| 3   | party_id       | `-p`   | `--party_id`       | No       | Party ID       |
| 4   | component_name | `-cpn` | `--component_name` | No       | Component Name |
| 5   | status         | `-s`   | `--status`         | No       | Job Status     |

-   *Examples*:

``` bash
flow task query -j $JOB_ID -p 9999 -r guest
flow task query -cpn hetero_feature_binning_0 -s complete
```

### `list`

-   *Description*: List tasks.
-   *Arguments*:

| No. | Argument | Flag_1 | Flag_2    | Required | Description                                |
| --- | -------- | ------ | --------- | -------- | ------------------------------------------ |
| 1   | limit    | `-l`   | `--limit` | No       | Number of records to return. (default: 10) |

-   *Examples*:

``` bash
flow task list
flow task list -l 25
```

## 11. Tag

### `create`

-   *Description*: Create tag.
-   *Arguments*:

| No. | Argument        | Flag_1 | Flag_2       | Required | Description            |
| --- | --------------- | ------ | ------------ | -------- | ---------------------- |
| 1   | tag_name        | `-t`   | `--tag-name` | Yes      | The name of tag        |
| 2   | tag_description | `-d`   | `--tag-desc` | No       | The description of tag |

-   *Examples*:

``` bash
flow tag create -t tag1 -d "This is the description of tag1."
flow tag create -t tag2
```

### `update`

-   *Description*: Update information of tag.
-   *Arguments*:

| No. | Argument            | Flag_1 | Flag_2           | Required | Description            |
| --- | ------------------- | ------ | ---------------- | -------- | ---------------------- |
| 1   | tag_name            | `-t`   | `--tag-name`     | Yes      | The name of tag        |
| 2   | new_tag_name        |        | `--new-tag-name` | No       | New name of tag        |
| 3   | new_tag_description |        | `--new-tag-desc` | No       | New description of tag |

-   *Examples*:

``` bash
flow tag update -t tag1 --new-tag-name tag2
flow tag update -t tag1 --new-tag-desc "This is the new description."
```

### `list`

-   *Description*: List recorded tags.
-   *Arguments*:

| No. | Argument | Flag_1 | Flag_2    | Required | Description                                |
| --- | -------- | ------ | --------- | -------- | ------------------------------------------ |
| 1   | limit    | `-l`   | `--limit` | No       | Number of records to return. (default: 10) |

-   *Examples*:

``` bash
flow tag list
flow tag list -l 3
```

### `query`

-   *Description*: Retrieve tag.
-   *Arguments*:

| No. | Argument   | Flag_1 | Flag_2         | Required | Description                                                                                  |
| --- | ---------- | ------ | -------------- | -------- | -------------------------------------------------------------------------------------------- |
| 1   | tag_name   | `-t`   | `--tag-name`   | Yes      | The name of tag                                                                              |
| 2   | with_model |        | `--with-model` | No       | If specified, the information of models which have the tag custom queried would be displayed |

-   *Examples*:

``` bash
flow tag query -t $TAG_NAME
flow tag query -t $TAG_NAME --with-model
```

### `delete`

-   *Description*: Delete tag.
-   *Arguments*:

| No. | Argument | Flag_1 | Flag_2       | Required | Description     |
| --- | -------- | ------ | ------------ | -------- | --------------- |
| 1   | tag_name | `-t`   | `--tag-name` | Yes      | The name of tag |

-   *Examples*:

``` bash
flow tag delete -t tag1
```

## 12. Queue

### `clean`

-   *Description*: Cancel all jobs in queue.
-   *Arguments*: None.
-   *Examples*:

``` bash
flow queue clean
```
