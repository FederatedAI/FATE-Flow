# Multi-Party Resource Coordination

## 1. Description

Resources refer to the basic engine resources, mainly CPU resources and memory resources of the compute engine, CPU resources and network resources of the transport engine, currently only the management of CPU resources of the compute engine is supported

## 2. Total resource allocation

- The current version does not automatically get the resource size of the base engine, so you configure it through the configuration file `$FATE_PROJECT_BASE/conf/service_conf.yaml`, that is, the resource size of the current engine allocated to the FATE cluster
- `FATE Flow Server` gets all the base engine information from the configuration file and registers it in the database table `t_engine_registry` when it starts.
- `FATE Flow Server` has been started and the resource configuration can be modified by restarting `FATE Flow Server` or by reloading the configuration using the command: `flow server reload`.
- `total_cores` = `nodes` * `cores_per_node`

**Example**

fate_on_standalone: is for executing a standalone engine on the same machine as `FATE Flow Server`, generally used for fast experiments, `nodes` is generally set to 1, `cores_per_node` is generally the number of CPU cores of the machine, also can be moderately over-provisioned

```yaml
fate_on_standalone:
  standalone:
    cores_per_node: 20
    nodes: 1
```

fate_on_eggroll: configured based on the actual deployment of `EggRoll` cluster, `nodes` denotes the number of `node manager` machines, `cores_per_node` denotes the average number of CPU cores per `node manager` machine

```yaml
fate_on_eggroll:
  clustermanager:
    cores_per_node: 16
    nodes: 1
  rollsite:
    host: 127.0.0.1
    port: 9370
```

fate_on_spark: configured based on the resources allocated to the `FATE` cluster in the `Spark` cluster, `nodes` indicates the number of `Spark` nodes, `cores_per_node` indicates the average number of CPU cores per node allocated to the `FATE` cluster

```yaml
fate_on_spark:
  spark:
    # default use SPARK_HOME environment variable
    home:
    cores_per_node: 20
    nodes: 2
```

Note: Please make sure that the `Spark` cluster allocates the corresponding amount of resources to the `FATE` cluster, if the `Spark` cluster allocates less resources than the resources configured in `FATE` here, then it will be possible to submit the `FATE` job, but when `FATE Flow` submits the task to the `Spark` cluster, the task will not actually execute because the `Spark` cluster has insufficient resources. Insufficient resources, the task is not actually executed

## 3. Job request resource configuration

We generally use ``task_cores`'' and ``task_parallelism`' to configure job request resources, such as

```json
{
"job_parameters": {
  "common": {
    "job_type": "train",
    "task_cores": 6,
    "task_parallelism": 2,
    "computing_partitions": 8,
    "timeout": 36000
    }
  }
}
```

The total resources requested by the job are `task_cores` * `task_parallelism`. When creating a job, `FATE Flow` will distribute the job to each `party` based on the above configuration, running role, and the engine used by the party (via `$FATE_PROJECT_BASE/conf/service_conf .yaml#default_engines`), the actual parameters will be calculated as follows

## 4. The process of calculating the actual parameter adaptation for resource requests

- Calculate `request_task_cores`:
  - guest, host.
    - `request_task_cores` = `task_cores`
  - arbiter, considering that the actual operation consumes very few resources: `request_task_cores
    - `request_task_cores` = 1

- Further calculate `task_cores_per_node`.
  - `task_cores_per_node"` = max(1, `request_task_cores` / `task_nodes`)

  - If `eggroll_run` or `spark_run` configuration resource is used in the above `job_parameters`, then the `task_cores` configuration is invalid; calculate `task_cores_per_node`.
    - `task_cores_per_node"` = eggroll_run["eggroll.session.processors.per.node"]
    - `task_cores_per_node"` = spark_run["executor-cores"]

- The parameter to convert to the adaptation engine (which will be presented to the compute engine for recognition when running the task).
  - fate_on_standalone/fate_on_eggroll:
    - eggroll_run["eggroll.session.processors.per.node"] = `task_cores_per_node`
  - fate_on_spark:
    - spark_run["num-executors"] = `task_nodes`
    - spark_run["executor-cores"] = `task_cores_per_node`

- The final calculation can be seen in the job's `job_runtime_conf_on_party.json`, typically in `$FATE_PROJECT_BASE/jobs/$job_id/$role/$party_id/job_runtime_on_party_conf.json `

## 5. Resource Scheduling Policy
- `total_cores` see [total_resource_allocation](#2-total-resource-allocation)
- `apply_cores` see [job_request_resource_configuration](#3-job-request-resource-configuration), `apply_cores` = `task_nodes` * `task_cores_per_node` * `task_parallelism`
- If all participants apply for resources successfully (total_cores - apply_cores) > 0, then the job applies for resources successfully
- If not all participants apply for resources successfully, then send a resource rollback command to the participants who have applied successfully, and the job fails to apply for resources

## 6. Related commands

{{snippet('cli/resource.md', header=False)}}
