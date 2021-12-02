## Server

### versions

List all relevant system version numbers

```bash
flow server versions
```

**Options**

None

**Returns**

| parameter name | type | description |
| :------ | :----- | -------- |
| retcode | int | return code |
| retmsg | string | return message |
| data | dict | return data |
| jobId | string | job id |

**Example**

```bash
flow server versions
```

Output:

```json
{
    "data": {
        "API": "v1",
        "CENTOS": "7.2",
        "EGGROLL": "2.4.0",
        "FATE": "1.7.0",
        "FATEBoard": "1.7.0",
        "FATEFlow": "1.7.0",
        "JDK": "8",
        "MAVEN": "3.6.3",
        "PYTHON": "3.6.5",
        "SPARK": "2.4.1",
        "UBUNTU": "16.04"
    },
    "retcode": 0,
    "retmsg": "success"
}
```

### reload

The following configuration items will take effect again after `reload`

  - All configurations after # engine services in $FATE_PROJECT_BASE/conf/service_conf.yaml
  - All configurations in $FATE_FLOW_BASE/python/fate_flow/job_default_config.yaml

```bash
flow server reload
```

**Options**

None

**Returns**

| parameter name | type | description |
| :------ | :----- | -------- |
| retcode | int | return code |
| retmsg | string | return message |
| data | dict | return data |
| jobId | string | job id |

**Example**

```bash
flow server reload
```

Output:

```json
{
    "data": {
        "job_default_config": {
            "auto_retries": 0,
            "auto_retry_delay": 1,
            "default_component_provider_path": "component_plugins/fate/python/federatedml",
            "end_status_job_scheduling_time_limit": 300000,
            "end_status_job_scheduling_updates": 1,
            "federated_command_trys": 3,
            "federated_status_collect_type": "PUSH",
            "job_timeout": 259200,
            "max_cores_percent_per_job": 1,
            "output_data_summary_count_limit": 100,
            "remote_request_timeout": 30000,
            "task_cores": 4,
            "task_memory": 0,
            "task_parallelism": 1,
            "total_cores_overweight_percent": 1,
            "total_memory_overweight_percent": 1,
            "upload_max_bytes": 4194304000
        },
        "service_registry": null
    },
    "retcode": 0,
    "retmsg": "success"
}
```
