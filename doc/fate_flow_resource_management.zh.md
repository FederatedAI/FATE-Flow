# FATE Flow 资源管理
[TOC]

## 1. 版本历史
| 版本状态 | 创建人     |   完成日期 | 备注 |
| :------- | :--------- | ---------: | :--- |
| 1.0      | jarviszeng | 2021-11-01 | 初始 |

## 2. 概述

资源指基础引擎资源，主要指计算引擎的CPU资源和内存资源，传输引擎的CPU资源和网络资源，目前仅支持计算引擎CPU资源的管理

## 2. 总资源配置

- 当前版本未实现自动获取基础引擎的资源大小，因此你通过配置文件`$PROJECT_BASE/conf/service_conf.yaml`进行配置，也即当前引擎分配给FATE集群的资源大小
- `FATE Flow Server`启动时从配置文件获取所有基础引擎信息并注册到数据库表`t_engine_registry`
- `FATE Flow Server`已经启动，修改资源配置，可重启`FATE Flow Server`，也可使用命令：`flow server reload`，重新加载配置
- `total_cores` = `nodes` * `cores_per_node`

**样例**

fate_on_standalone：是为执行在`FATE Flow Server`同台机器的单机引擎，一般用于快速实验，`nodes`一般设置为1，`cores_per_node`一般为机器CPU核数，也可适量超配

```json
fate_on_standalone:
  standalone:
    cores_per_node: 20
    nodes: 1
```

fate_on_eggroll：依据`EggRoll`集群实际部署情况进行配置，`nodes`表示`node manager`的机器数量，`cores_per_node`表示平均每台`node manager`机器CPU核数

```json
fate_on_eggroll:
  clustermanager:
    cores_per_node: 16
    nodes: 1
  rollsite:
    host: 127.0.0.1
    port: 9370
```

fate_on_spark：依据在`Spark`集群中配置给`FATE`集群的资源进行配置，`nodes`表示`Spark`节点数量，`cores_per_node`表示平均每个节点分配给`FATE`集群的CPU核数

```json
fate_on_spark:
  spark:
    # default use SPARK_HOME environment variable
    home:
    cores_per_node: 20
    nodes: 2
```

注意：请务必确保在`Spark`集群分配了对应数量的资源于`FATE`集群，若`Spark`集群分配资源少于此处`FATE`所配置的资源，那么会出现可以提交`FATE`作业，但是`FATE Flow`将任务提交至`Spark`集群时，由于`Spark`集群资源不足，任务实际不执行

## 3. 作业申请资源配置

我们一般使用`task_cores`和`task_parallelism`进行配置作业申请资源，如：

```json
"job_parameters": {
  "common": {
    "job_type": "train",
    "task_cores": 6,
    "task_parallelism": 2,
    "computing_partitions": 8,
    "timeout": 36000
  }
}
```

作业申请的总资源为`task_cores` * `task_parallelism`，创建作业时，`FATE Flow`分发作业到各`party`时会依据上述配置、运行角色、本方使用引擎(通过`$PROJECT_BASE/conf/service_conf.yaml#default_engines`)，适配计算出实际参数，如下

## 4. 资源申请实际参数适配计算过程

- 计算`request_task_cores`:
  - guest、host：
    - `request_task_cores` = `task_cores`
  - arbiter，考虑实际运行耗费极少资源：
    - `request_task_cores` = 1

- 进一步计算`task_cores_per_node`：
  - `task_cores_per_node"` = max(1, `request_task_cores` / `task_nodes`)

  - 若在上述`job_parameters`使用了`eggroll_run`或`spark_run`配置资源时，则`task_cores`配置无效；计算`task_cores_per_node`：
    - `task_cores_per_node"` = eggroll_run[“eggroll.session.processors.per.node”]
    - `task_cores_per_node"` = spark_run["executor-cores"]

- 转换为适配引擎的参数(该参数会在运行任务时，提交到计算引擎识别)：
  - fate_on_standalone/fate_on_eggroll:
    - eggroll_run["eggroll.session.processors.per.node"] = `task_cores_per_node`
  - fate_on_spark:
    - spark_run["num-executors"] = `task_nodes`
    - spark_run["executor-cores"] = `task_cores_per_node`

- 最终计算结果可以查看job的`job_runtime_conf_on_party.json`，一般在`$PROJECT_BASE/jobs/$job_id/$role/$party_id/job_runtime_on_party_conf.json`

## 5. 资源调度策略

- `total_cores`见上述[总资源配置](#41-总资源配置)
- `apply_cores`见上述[作业申请资源配置](#42-作业申请资源配置)，`apply_cores` = `task_nodes` * `task_cores_per_node` * `task_parallelism`
- 若所有参与方均申请资源成功(total_cores - apply_cores) > 0，则该作业申请资源成功
- 若非所有参与方均申请资源成功，则发送资源回滚指令到已申请成功的参与方，该作业申请资源失败

## 6. 相关命令

### 6.1 资源查询

**请求CLI** 

```bash
flow resource query
```

**简要描述：** 

- 用于查询fate系统资源

**请求参数** 

无

**返回参数** 

| 参数名  | 类型   | 说明     |
| :------ | :----- | -------- |
| retcode | int    | 返回码   |
| retmsg  | string | 返回信息 |
| data    | object | 返回数据 |

样例：

```
{
    "data": {
        "computing_engine_resource": {
            "f_cores": 32,
            "f_create_date": "2021-09-21 19:32:59",
            "f_create_time": 1632223979564,
            "f_engine_config": {
                "cores_per_node": 32,
                "nodes": 1
            },
            "f_engine_entrance": "fate_on_eggroll",
            "f_engine_name": "EGGROLL",
            "f_engine_type": "computing",
            "f_memory": 0,
            "f_nodes": 1,
            "f_remaining_cores": 32,
            "f_remaining_memory": 0,
            "f_update_date": "2021-11-08 16:56:38",
            "f_update_time": 1636361798812
        },
        "use_resource_job": []
    },
    "retcode": 0,
    "retmsg": "success"
}
```

### 6.2 资源归还

**请求CLI** 

```bash
flow resource return -j $JobId
```

**简要描述：** 

- 用于归还某个job的资源

**请求参数** 

| 参数名 | 必选 | 类型   | 说明   |
| :----- | :--- | :----- | ------ |
| job_id | 是   | string | 任务id |

**返回参数** 

| 参数名  | 类型   | 说明     |
| :------ | :----- | -------- |
| retcode | int    | 返回码   |
| retmsg  | string | 返回信息 |
| data    | object | 返回数据 |

样例：

```json
{
    "data": [
        {
            "job_id": "202111081612427726750",
            "party_id": "8888",
            "resource_in_use": true,
            "resource_return_status": true,
            "role": "guest"
        }
    ],
    "retcode": 0,
    "retmsg": "success"
}
```
