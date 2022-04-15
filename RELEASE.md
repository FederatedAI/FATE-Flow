# Release 1.8.0
## Major Features and Improvements
Optimize the model migration function to reduce user operation steps;
Add version compatibility check in component center to support multiple parties to use different versions;
Add data table disable/enable function, and support batch delete disable table

# Release 1.7.2
## Major Features and Improvements
* Separate the base connection address of the data storage table from the data table information, and compatible with historical versions;
* Optimize the component output data download interface.

# Release 1.7.1
## Major Features and Improvements
* Added the writer component, which supports exporting data to mysql and saving data as a new table;
* Added job reuse function, which supports the reuse of successful status components of historical tasks in new jobs;
* Optimize the time-consuming problem of submitting tasks and the time-consuming problem of stopping tasks;
* Component registration supports automatic setting of PYTHONPYTH.

## Bug Fixes
* Fix the problem of OOM when uploading hdfs table;
* Fix the problem of incompatibility with the old version of serving;
* The parameter partitions of the toy test is set to 4, and a timeout prompt is added.

# Release 1.7.0

## Major Features and Improvements

* Independent repository instead of all code in the main FATE repository
* Component registry, which can hot load many different versions of component packages at the same time
* Hot update of component parameters, component-specific reruns, automatic reruns
* Model Checkpoint to support task hot start, model deployment and other
* Data, Model and Cache can be reused between jobs
* Reader component supports more data sources, such as MySQL, Hive
* Realtime recording of dataset usage derivation routes
* Multi-party permission control for datasets
* Automatic push to reliable storage when model deployment, support Tencent Cloud COS, MySQL, Redis
* REST API authentication

## Bug Fixes

# Release 1.6.1
## Major Features and Improvements
* Support mysql storage engine;
* Added service registry interface;
* Added service query interface;
* Support fate on WeDataSphere mode
* Add lock when writing `model_local_cache`
* Register the model download urls to zookeeper

## Bug Fixes
* Fix job id length no more than 25 limitation


# Release 1.5.2
## Major Features and Improvements
* Read data from mysql with ‘table bind’ command to map source table to FATE table
* FATE cluster push model for one-to-multiple FATE Serving clusters in one party

## Bug Fixes
* Fix job id length no more than 25 limitation


# Release 1.5.1
## Major Features and Improvements
* Optimize the model center, reconstruct publishing model, support deploy, load, bind, migrate operations, and add new interfaces such as model info
* Improve identity authentication and resource authorization, support party identity verification, and participate in the authorization of roles and components
* Optimize and fix resource manager, add task_cores job parameters to adapt to different computing engines

## Deploy
* Support 1.5.0 retain data upgrade to 1.5.1

## Bug Fixes
* Fix job clean CLI


# Release 1.5.0（LTS）
## Major Features and Improvements
* Brand new scheduling framework based on global state and optimistic concurrency control and support multiple scheduler
* Upgraded task scheduling: multi-model output for component, executing component in parallel, component rerun
* Add new DSL v2 which significantly improves user experiences in comparison to DSL v1. Several syntax error detection functions are supported in v2. Now DSL v1 and v2 are 
   compatible in the current FATE version
* Enhanced resource scheduling: remove limit on job number, base on cores, memory and working node according to different computing engine supports
* Add model registry, supports model query, import/export, model transfer between clusters
* Add Reader component: automatically dump input data to FATE-compatible format and cluster storage engine; now data from HDFS
* Refactor submit job configuration's parameters setting, support different parties use different job parameters when using dsl V2.

## Client
* Brand new CLI v2 with easy independent installation, user-friendly programming syntax & command-line prompt
* Support FLOW python language SDK


# Release 1.4.4
## Major Features and Improvements
* Task Executor supports monkey patch
* Add forward API


# Release 1.4.2
## Major Features and Improvements
* Distinguish between user stop job and system stop job;
* Optimized some logs;
* Optimize zookeeper configuration
* The model supports persistent storage to mysql
* Push the model to the online service to support the specified storage address (local file and FATEFlowServer interface)


# Release 1.4.1
## Major Features and Improvements
* Allow the host to stop the job
* Optimize the task queue
* Automatically align the input table partitions of all participants when the job is running
* Fate flow client large file upload optimization
* Fixed some bugs with abnormal status


# Release 1.4.0
## Major Features and Improvements
* Refactoring model management, native file directory storage, storage structure is more flexible, more information
* Support model import and export, store and restore with reliable distributed system(Redis is currently supported)
* Using MySQL instead of Redis to implement Job Queue, reducing system complexity
* Support for uploading client local files
* Automatically detects the existence of the table and provides the destroy option
* Separate system, algorithm, scheduling command log, scheduling command log can be independently audited


# Release 1.3.1
## Major Features and Improvements
## Deploy
* Support deploying by MacOS
* Support using external db
* Deploy JDK and Python environments on demand
* Improve MySQL and FATE Flow service.sh
* Support more custom deployment configurations in the default_configurations.sh, such as ssh_port, mysql_port and so one.

# Release 1.3.0
## Major Features and Improvements
* Add clean job CLI for cleaning output and intermediate results, including data, metrics and sessions
* Support for obtaining table namespace and name of output data via CLI
* Fix KillJob unsuccessful execution in some special cases
* Improve log system, add more exception and run time status prompts


# Release 1.2.0
## Major Features and Improvements
* Add data management module for recording the uploaded data tables and the outputs of the model in the job running, and for querying and cleaning up CLI. 
* Support registration center for simplifying communication configuration between FATEFlow and FATEServing
* Restruct model release logic, FATE_Flow pushes model directly to FATE-Serving. Decouple FATE-Serving and Eggroll, and the offline and online architectures are connected only by FATE-Flow.
* Provide CLI to query data upload record
* Upload and download data support progress statistics by line
* Add some abnormal diagnosis tips
* Support adding note information to job

## Deploy
* Fix bugs in EggRoll startup script, add mysql, redis startup options.
* Disable host name resolution configuration for mysql service.
* The version number of each module of the software packaging script is updated using the automatic acquisition mode.


# Release 1.1.1
## Major Features and Improvements
* Add cluster deployment support based on ubuntu operating system。
* Support intermediate data cleanup after the task ends
* Optimizing the deployment process


## Bug Fixes
* Fix a bug in download api
* Fix bugs of spark-backend


# Release 1.1
## Major Features and Improvements
* Upload and Download support CLI for querying job status
* Support for canceling waiting job
* Support for setting job timeout
* Support for storing a job scheduling log in the job log folder
* Add authentication control Beta version, including component, command, role


# Release 1.0.2
## Major Features and Improvements
* Python and JDK environment are required only for running standalone version quick experiment
* Support cluster version docker deployment
* Add deployment guide in Chinese
* Standalone version job for quick experiment is supported when cluster version deployed. 
* Python service log will remain for 14 days now.


# Release 1.0.1
## Bug Fixes
* Support upload file in version argument
* Support get serviceRoleName from configuration


# Release 1.0
## Major Features and Improvements
* DAG defines Pipeline
* Federated Multi-party asymmetric DSL parser
* Federated Learning lifecycle management
* Federated Task collaborative scheduling
* Tracking for data, metric, model and so on
* Federated Multi-party model management