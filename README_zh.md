---
FATE FLOW
---

简介
====

FATE-Flow是联邦学习框架FATE的作业调度系统，实现联邦学习作业生命周期的完整管理，其中包括数据输入、训练作业调度、指标追踪、模型中心等功能.

![FATE-Flow联邦学习Pipeline](images/federated_learning_pipeline.png)

FATE-Flow主要功能:
------------------

-   使用DAG定义Pipeline；
-   使用 JSON 格式的 FATE-DSL 描述DAG, 支持系统自动化对接；
-   先进的调度框架，基于全局状态和乐观锁调度，单方DAG调度，多方协调调度，并支持多调度器
-   灵活的调度策略，支持启动/停止/重跑等
-   细粒度的资源调度能力，依据不同计算引擎支持核数、内存、工作节点策略
-   实时追踪器，运行期间实时跟踪数据, 参数, 模型和指标
-   联邦模型中心, 模型管理、联邦一致性、导入导出、集群间迁移
-   提供CLI、HTTP API、Python SDK

[Wiki](https://github.com/FederatedAI/FATE-Flow/wiki)
------------

[部署](../../README_zh.md)
====

用法
====

##### [命令行](../fate_client/flow_client/README_zh.rst)

##### [Python SDK](../fate_client/flow_sdk/README_zh.rst)

##### [HTTP API](doc/fate_flow_http_api.rst)

##### [训练样例](examples/README_zh.rst)

##### [在线推理样例](../../doc/model_publish_with_serving_guide_zh.md)