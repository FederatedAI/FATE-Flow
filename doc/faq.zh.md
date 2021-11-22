# 常见问题

## 1. 说明

## 2. 日志说明

一般来说，排查问题，需要如下几个日志：

### v1.7+

- `${FATE_PROJECT_BASE}/fateflow/logs/$job_id/fate_flow_schedule.log`，这个是某个任务的内部调度日志

- `${FATE_PROJECT_BASE}/fateflow/logs/$job_id/*` 这些是某个任务的所有执行日志

- `${FATE_PROJECT_BASE}/fateflow/logs/fate_flow/fate_flow_stat.log`，这个是与任务无关的一些日志

- `${FATE_PROJECT_BASE}/fateflow/logs/fate_flow/fate_flow_schedule.log`，这个是所有任务的整体调度日志

- `${FATE_PROJECT_BASE}/fateflow/logs/fate_flow/fate_flow_detect.log`，这个是所有任务的整体异常探测日志

### v1.7-

- `${FATE_PROJECT_BASE}/logs/$job_id/fate_flow_schedule.log`，这个是某个任务的内部调度日志

- `${FATE_PROJECT_BASE}/logs/$job_id/*` 这些是某个任务的所有执行日志

- `${FATE_PROJECT_BASE}/logs/fate_flow/fate_flow_stat.log`，这个是与任务无关的一些日志

- `${FATE_PROJECT_BASE}/logs/fate_flow/fate_flow_schedule.log`，这个是所有任务的整体调度日志

- `${FATE_PROJECT_BASE}/logs/fate_flow/fate_flow_detect.log`，这个是所有任务的整体异常探测日志

## 3. 离线部分

### upload失败

- 检查eggroll相关服务是否异常；

### 提交任务(submit_job)卡住

- 检查双方rollsite服务是否被kill了

### 提交任务(submit_job)返回grpc异常

- 提交任务的链路： guest fate_flow -> guest rollsite -> host rollsite -> host fate_flow
- 检查上面的链路中的每个服务是否挂了，必须保证每个节点都正常运行；
- 检查路由表的配置是否正确；

### dataio组件异常: not enough values to unpack (expected 2, got 1)

- 数据的分隔符和配置中的分割符不一致

### 任务运行时抛出异常:"Count of data_instance is 0"

- 任务中有交集组件并且交集匹配率为0，需要检查guest和host的输出数据id是否能匹配上；

## 4. 在线部分

### 推模型(load)retcode返回100，可能的原因有哪些？

- 没有部署fate-servings

- flow没有获取到fate-servings的地址

- flow读取fate-servings的地址的优先级排序: 

  1. 从zk读取

  2. 没有打开zk的话，会从fate的服务配置文件读取，配置路径在

     - 1.5+: `${FATE_PROJECT_BASE}/conf/service_conf.yaml`

     - 1.5-: `${FATE_PROJECT_BASE}/arch/conf/server_conf.json`

### 推模型(load)retcode返回123，可能原因有哪些？

- 模型信息有误；
- 此错误码是fate-servings没有找到模型而抛出的；

### 绑定模型(bind)操作时提示"no service id"?

- 在bind配置中自定义service_id

### servings的配置在哪?怎么配？

- 1.5+ 配置路径: `${FATE_PROJECT_BASE}/conf/service_conf.yaml`

```yaml
servings:
  hosts:
    - 127.0.0.1:8000
```

- 1.5- 配置路径: `${FATE_PROJECT_BASE}/arch/conf/server_conf.json`

```json
{
    "servers": {
        "servings": ["127.0.0.1:8000"]
    }
}
```
