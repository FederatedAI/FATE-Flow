# FAQ

## 1. Description

## 2. Log descriptions

In general, to troubleshoot a problem, the following logs are required.

## v1.7+

- `${FATE_PROJECT_BASE}/fateflow/logs/$job_id/fate_flow_schedule.log`, this is the internal scheduling log of a certain task

- `${FATE_PROJECT_BASE}/fateflow/logs/$job_id/*` These are all the execution logs of a certain task

- `${FATE_PROJECT_BASE}/fateflow/logs/fate_flow/fate_flow_stat.log`, this is some logs that are not related to tasks

- `${FATE_PROJECT_BASE}/fateflow/logs/fate_flow/fate_flow_schedule.log`, this is the overall scheduling log of all tasks

- `${FATE_PROJECT_BASE}/fateflow/logs/fate_flow/fate_flow_detect.log`, which is the overall exception detection log for all tasks

### v1.7-

- `${FATE_PROJECT_BASE}/logs/$job_id/fate_flow_schedule.log`, this is the internal scheduling log for a particular task

- `${FATE_PROJECT_BASE}/logs/$job_id/*` These are all the execution logs of a certain task

- `${FATE_PROJECT_BASE}/logs/fate_flow/fate_flow_stat.log`, this is some logs that are not related to the task

- `${FATE_PROJECT_BASE}/logs/fate_flow/fate_flow_schedule.log`, this is the overall scheduling log of all tasks

- `${FATE_PROJECT_BASE}/logs/fate_flow/fate_flow_detect.log`, this is the overall exception detection log of all tasks

## 3. Offline

### upload failed

- checking eggroll related services for exceptions.

### submit job is stuck

- check if both rollsite services have been killed

### submit_job returns grpc exception

- submit job link: guest fate_flow -> guest rollsite -> host rollsite -> host fate_flow
- check that each service in the above link is not hung, it must be ensured that each node is functioning properly.
- checking that the routing table is correctly configured.

### dataio component exception: not enough values to unpack (expected 2, got 1)

- the data separator does not match the separator in the configuration

### Exception thrown at task runtime: "Count of data_instance is 0"

- task has an intersection component and the intersection match rate is 0, need to check if the output data ids of guest and host can be matched.

## 4. Serving

### load model retcode returns 100, what are the possible reasons?

- no fate-servings deployed

- flow did not fetch the fate-servings address

- flow reads the address of the fate-servings in priority order:

  1. read from zk

  2. if zk is not open, it will read from the fate-servings configuration file, the configuration path is

     - 1.5+: `${FATE_PROJECT_BASE}/conf/service_conf.yaml`

     - 1.5-: `${FATE_PROJECT_BASE}/arch/conf/server_conf.json`

### load model retcode returns 123, what are the possible reasons?

- Incorrect model information.
- This error code is thrown by fate-servings not finding the model.

### bind model operation prompted "no service id"?

- Customize the service_id in the bind configuration

### Where is the configuration of servings? How do I configure it?

- v1.5+ Configuration path: `${FATE_PROJECT_BASE}/conf/service_conf.yaml`

```yaml
servings:
  hosts:
    - 127.0.0.1:8000
```

- v1.5- Configuration path: `${FATE_PROJECT_BASE}/arch/conf/server_conf.json`

```json
{
    "servers": {
        "servings": ["127.0.0.1:8000"]
    }
}
```
