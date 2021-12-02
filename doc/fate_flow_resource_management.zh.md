# 多方资源协调

## 1. 说明

资源指基础引擎资源，主要指计算引擎的CPU资源和内存资源，传输引擎的CPU资源和网络资源，目前仅支持计算引擎CPU资源的管理

## 2. 总资源配置

- 当前版本未实现自动获取基础引擎的资源大小，因此你通过配置文件`$FATE_PROJECT_BASE/conf/service_conf.yaml`进行配置，也即当前引擎分配给FATE集群的资源大小
- `FATE Flow Server`启动时从配置文件获取所有基础引擎信息并注册到数据库表`t_engine_registry`
- `FATE Flow Server`已经启动，修改资源配置，可重启`FATE Flow Server`，也可使用命令：`flow server reload`，重新加载配置
- `total_cores` = `nodes` * `cores_per_node`

**样例**

fate_on_standalone：是为执行在`FATE Flow Server`同台机器的单机引擎，一般用于快速实验，`nodes`一般设置为1，`cores_per_node`一般为机器CPU核数，也可适量超配

```yaml
fate_on_standalone:
  standalone:
    cores_per_node: 20
    nodes: 1
```

fate_on_eggroll：依据`EggRoll`集群实际部署情况进行配置，`nodes`表示`node manager`的机器数量，`cores_per_node`表示平均每台`node manager`机器CPU核数

```yaml
fate_on_eggroll:
  clustermanager:
    cores_per_node: 16
    nodes: 1
  rollsite:
    host: 127.0.0.1
    port: 9370
```

fate_on_spark：依据在`Spark`集群中配置给`FATE`集群的资源进行配置，`nodes`表示`Spark`节点数量，`cores_per_node`表示平均每个节点分配给`FATE`集群的CPU核数

```yaml
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

作业申请的总资源为`task_cores` * `task_parallelism`，创建作业时，`FATE Flow`分发作业到各`party`时会依据上述配置、运行角色、本方使用引擎(通过`$FATE_PROJECT_BASE/conf/service_conf.yaml#default_engines`)，适配计算出实际参数，如下

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

- 最终计算结果可以查看job的`job_runtime_conf_on_party.json`，一般在`$FATE_PROJECT_BASE/jobs/$job_id/$role/$party_id/job_runtime_on_party_conf.json`

## 5. 资源调度策略

- `total_cores`见上述[总资源配置](#2-总资源配置)
- `apply_cores`见上述[作业申请资源配置](#3-作业申请资源配置)，`apply_cores` = `task_nodes` * `task_cores_per_node` * `task_parallelism`
- 若所有参与方均申请资源成功(total_cores - apply_cores) > 0，则该作业申请资源成功
- 若非所有参与方均申请资源成功，则发送资源回滚指令到已申请成功的参与方，该作业申请资源失败

## 6. 相关命令

{{snippet('cli/resource.zh.md', header=False)}}
