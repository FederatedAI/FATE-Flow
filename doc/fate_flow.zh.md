# 整体设计

## 1. 逻辑架构

- DSL定义作业
- 自顶向下的纵向子任务流调度、多参与方联合子任务协调
- 独立隔离的任务执行工作进程
- 支持多类型多版本组件
- 计算抽象API
- 存储抽象API
- 跨方传输抽象API

![](./images/fate_flow_logical_arch.png)

## 2. 整体架构

### 2.1 FATE整体架构

![](./images/fate_arch.png)

### 2.2 FATE Flow整体架构

![](./images/fate_flow_arch.png)

## 3. [调度架构](./fate_flow_job_scheduling.zh.md)

### 3.1 基于共享状态的全新调度架构

- 剥离状态(资源、作业)与管理器(调度器、资源管理器)
- 资源状态与作业状态持久化存于MySQL，全局共享，提供可靠事务性操作
- 提高管理服务的高可用与扩展性
- 作业可介入，支持实现如重启、重跑、并行控制、资源隔离等

![](./images/fate_flow_scheduling_arch.png)

### 3.2 状态驱动调度

- 资源协调
- 拉起子进程Executor运行组件
- Executor上报状态到本方Server，并且同时上报到调度方
- 多方任务状态计算联邦任务状态
- 上下游任务状态计算作业作态

![](./images/fate_flow_resource_process.png)

## 4. [多方资源协调](./fate_flow_resource_management.zh.md)

- 每个引擎总资源大小通过配置文件配置，后续实现系统对接
- 总资源大小中的cores_per_node表示每个计算节点cpu核数，nodes表示计算节点个数
- FATEFlow server启动时从配置文件读取资源大小配置，并注册更新到数据库
- 以Job维度申请资源，Job Conf提交时生效，公式：task_parallelism*task_cores
- 详细请看文档单独章节

## 5. [数据流动追踪](./fate_flow_tracking.zh.md)

- 定义
 - metric type: 指标类型，如auc, loss, ks等等
 - metric namespace: 自定义指标命名空间，如train, predict
 - metric name: 自定义指标名称，如auc0，hetero_lr_auc0
 - metric data: key-value形式的指标数据
 - metric meta: key-value形式的指标元信息，支持灵活画图
- API
 - log_metric_data(metric_namespace, metric_name, metrics)
 - set_metric_meta(metric_namespace, metric_name, metric_meta)
 - get_metric_data(metric_namespace, metric_name)
 - get_metric_meta(metric_namespace, metric_name)

## 6. [作业实时监测](./fate_flow_monitoring.zh.md)

- 工作进程存活性检测
- 作业超时检测
- 资源回收检测
- 基础引擎会话超时检测

![](./images/fate_flow_detector.png)

## 7. [任务组件中心](./fate_flow_component_registry.zh.md)

![](./images/fate_flow_component_registry.png)

## 8. [多方联合模型注册中心](./fate_flow_model_registry.zh.md)

- 使用Google Protocol Buffer作为模型存储协议，利用跨语言共享，每个算法模型由两部分组成：ModelParam & ModelMeta
- 一个Pipeline产生一系列算法模型
- 命名为Pipeline的模型存储Pipeline建模DSL及在线推理DSL
- 联邦学习下，需要保证所有参与方模型一致性，即模型绑定
- model_key为用户提交任务时定义的模型标识
- 联邦各方的模型ID由本方标识信息role、party_id，加model_key
- 联邦各方的模型版本必须唯一且保持一致，FATE-Flow直接设置为job_id

![](./images/fate_flow_pipelined_model.png){: style="height:400px;width:450px"}

![](./images/fate_flow_model_storage.png){: style="height:400px;width:800px"}

## 9. [数据接入](./fate_flow_data_access.zh.md)

- Upload：
 - 外部存储直接导入到FATE Storage，创建一个新的DTable
 - 作业运行时，Reader直接从Storage读取

- Table Bind：
 - 外部存储地址关键到FATE一个新的DTable
 - 作业运行时，Reader通过Meta从外部存储读取数据并转存到FATE Storage
 - 打通大数据生态：HDFS，Hive/MySQL

![](./images/fate_flow_inputoutput.png)

## 10. [多方合作权限管理](./fate_flow_authority_management.zh.md)

![](./images/fate_flow_authorization.png)
