# FATE Flow 服务端操作

[TOC]

## 1. 版本历史

| 版本状态 | 创建人     |   完成日期 | 备注 |
| :------- | :--------- | ---------: | :--- |
| 1.0      | jarviszeng | 2021-11-10 | 初始 |

## 2. 概述

主要介绍`FATE Flow Server`的一些常规操作

## 3. 查看版本信息

**请求CLI** 

```bash
flow server
```

**请求参数** 

无

**返回参数** 

| 参数名  | 类型   | 说明     |
| :------ | :----- | -------- |
| retcode | int    | 返回码   |
| retmsg  | string | 返回信息 |
| data    | dict   | 返回数据 |
| jobId   | string | 作业id   |

**样例** 

```bash
flow server versions
```

输出:

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

## 4. 重新加载配置文件

如下配置项在`reload`后会重新生效

- $PROJECT_BASE/conf/service_conf.yaml中# engine services后的所有配置
- $FATE_FLOW_BASE/python/fate_flow/job_default_config.yaml中所有配置

**请求CLI** 

```bash
flow server reload
```

**请求参数** 

无

**返回参数** 

| 参数名  | 类型   | 说明     |
| :------ | :----- | -------- |
| retcode | int    | 返回码   |
| retmsg  | string | 返回信息 |
| data    | dict   | 返回数据 |
| jobId   | string | 作业id   |

**样例** 

```bash
flow server reload
```

输出:

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
