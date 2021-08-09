English \| [中文](README_zh.md)

FATE FLOW
=========

Introduction
------------

FATE-Flow is the job scheduling system of the federated learning framework FATE, which realizes the complete management of the federated learning job life cycle, including data input, training job scheduling, indicator tracking, model center and other functions

![FATE-Flow Federated Learning Pipeline](images/federated_learning_pipeline.png)

### FATE-Flow now supports

-   DAG define Pipeline
-   Describe DAG using FATE-DSL in JSON format
-   Advanced scheduling framework, based on global state and optimistic lock scheduling, single-party DAG scheduling, multi-party coordinated scheduling, and support for multiple schedulers
-   Flexible scheduling strategy, support start/stop/rerun, etc.
-   Fine-grained resource scheduling capabilities, supporting core, memory, and working node strategies based on different computing engines
-   Realtime tracker, real-time tracking data, parameters, models and indicators during operation
-   Federated Learning Model Registry, model management, federated consistency, import and export, migration between clusters
-   Provide CLI, HTTP API, Python SDK

[Wiki](https://github.com/FederatedAI/FATE-Flow/wiki)
------------

[Deploy](../../README.md)
------

Usage
-----

##### [Command Line Interface v2](../fate_client/flow_client/README.rst)

##### [Python SDK](../fate_client/flow_sdk/README.rst)

##### [HTTP API](doc/fate_flow_http_api.rst)

##### [Training Examples](examples/README.rst)

##### [Online Inference Examples](../../doc/model_publish_with_serving_guide.md)