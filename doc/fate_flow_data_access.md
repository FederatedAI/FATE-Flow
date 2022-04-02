# Data Access

## 1. Description

- The storage tables of fate are identified by table name and namespace.

- fate provides an upload component for users to upload data to a storage system supported by the fate compute engine.

- If the user's data already exists in a storage system supported by fate, the storage information can be mapped to a fate storage table by table bind.

- If the table bind's table storage type is not consistent with the current default engine, the reader component will automatically convert the storage type;

  

## 2. data upload

{{snippet('cli/data.md', '### upload')}}

## 3. table binding

{{snippet('cli/table.md', '### bind')}}


## 4. table information query

{{snippet('cli/table.md', '### info')}}

## 5. Delete table data

{{snippet('cli/table.md', '### delete')}}



## 6. Download data

{{snippet('cli/data.md', '### download')}}

## 7.  disable data

{{snippet('cli/table.md', '### disable')}}

## 8.  enable data 

{{snippet('cli/table.md', '### enable')}}

## 9.  delete disable data 

{{snippet('cli/table.md', '### disable-delete')}}


## 10. Writer

{{snippet('cli/data.md', '### writer')}}


## 11. reader component

**Brief description:** 

- The reader component is a data input component of fate;
- The reader component converts input data into data of the specified storage type;

**Parameter configuration**:

The input table of the reader is configured in the conf when submitting the job:

```shell
{
  "role": {
    "guest": {
      "0": { "reader_0": { "table": { "name": "breast_hetero_guest", "namespace": "experiment"}
    }
  }
}

```

**Component Output**

The output data storage engine of the component is determined by the configuration file conf/service_conf.yaml, with the following configuration items:

```yaml
default_engines:
  storage: eggroll
```

- The computing engine and storage engine have certain support dependencies on each other, the list of dependencies is as follows.

  | computing_engine | storage_engine |
  | :--------------- | :---------------------------- |
  | standalone | standalone |
  | eggroll | eggroll |
  | spark | hdfs(distributed), localfs(standalone) |

- The reader component's input data storage type supports: eggroll, hdfs, localfs, mysql, path, etc;
- reader component output data type is determined by default_engines.storage configuration (except for path)

