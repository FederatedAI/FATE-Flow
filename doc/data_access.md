# FATE Data Access Guide

## 1. Upload Process
The process diagram for data upload is as follows:

![Data Upload](./images/upload_data.png)
- The client uploads data to the server.
- The server encapsulates the upload parameters into a DAG job configuration, including two components: 'upload' and 'dataframe-transformer,' then calls the submit interface to submit the job.
- The 'upload' component stores data into the FATE storage service.
- The 'transformer' component converts the data output from the 'upload' component into a dataframe and stores it into the FATE storage service.
- Metadata about the data is stored in the database.

## 2. Data Upload Methods
Note: FATE provides clients including SDK, CLI, and Pipeline. If you haven't deployed the FATE Client in your environment, you can use `pip install fate_client` to download it. The following operations are CLI-based.

### 2.1 Upload Scenario Explanation
- Client-server separation: Installed client and server are on different machines.
- Client-server non-separation: Installed client and server are on the same machine.
Difference: In scenarios where the client and server are not separated, the step "the client uploads data to the server" in the above process can be omitted to improve data upload efficiency in scenarios with large data volumes. There are differences in interfaces and parameters between the two scenarios, and you can choose the corresponding scenario for data upload.

### 2.2 Data Upload
#### 2.2.1 Configuration and Data Preparation
 - Upload configuration is located in [examples-upload](https://github.com/FederatedAI/FATE-Flow/tree/v2.0.0/examples/upload)
    ```yaml
    {
      "file": "examples/data/breast_hetero_guest.csv",
      "head": true,
      "partitions": 16,
      "extend_sid": true,
      "meta": {
        "delimiter": ",",
        "label_name": "y",
        "match_id_name": "id"
      },
      "namespace": "experiment",
      "name": "breast_hetero_guest"
    }
    ```
   - file: File path
   - head: Whether the data contains a header: true/false
   - partitions: Number of data storage partitions
   - extend_sid: Whether to generate an 'sid' column
   - meta: Metadata about the data
   - namespace && name: Reference to data in the FATE storage table
 - Uploaded data is located in [upload-data](https://github.com/FederatedAI/FATE-Flow/tree/v2.0.0/examples/data)
 - You can also use your own data and modify the "meta" information in the upload configuration.

#### 2.2.2 Data Upload Commands
##### Client-Server Non-Separation
```shell
flow data upload -c examples/upload/upload_guest.json
```
Note: Ensure that the file path in the configuration exists on the server.
##### Client-Server Separation
```shell
flow data upload-file -c examples/upload/upload_guest.json
```
#### 2.2.3 Upload Results
```json
{
    "code": 0,
    "data": {
        "name": "breast_hetero_guest",
        "namespace": "experiment"
    },
    "job_id": "202312281606030428210",
    "message": "success"
}
```

#### 2.2.4 Data Query
Since the entire upload is an asynchronous operation, it's necessary to confirm successful upload before performing subsequent operations.
```shell
flow table query --namespace experiment --name breast_hetero_guest
```
- Successful data upload returns:
```json
{
    "code": 0,
    "data": {
        "count": 569,
        "data_type": "dataframe",
        "engine": "standalone",
        "meta": {},
        "name": "breast_hetero_guest",
        "namespace": "experiment",
        "path": "xxx",
        "source": {
            "component": "dataframe_transformer",
            "output_artifact_key": "dataframe_output",
            "output_index": null,
            "party_task_id": "202312281606030428210_transformer_0_0_local_0",
            "task_id": "202312281606030428210_transformer_0",
            "task_name": "transformer_0"
        }
    },
    "message": "success"
}
```

## 3. Data Binding
For specific algorithms that may require particular datasets, FATE Flow provides a data binding interface to make the data available for use in FATE.

```shell
flow table bind --namespace bind_data --name breast_hetero_guest --path /data/projects/fate/fate_flow/data/xxx
```

## 4. Data Query
For uploaded or bound data tables, you can use the query interface to retrieve brief information about the data.

```shell
flow table query --namespace experiment --name breast_hetero_guest
```

## 5. Data Cleaning
You can use delete cli to clean data tables that already exist in FATE.

```shell
flow table delete --namespace experiment --name breast_hetero_guest
```
