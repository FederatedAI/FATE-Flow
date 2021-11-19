# 任务组件注册中心

## 1. 说明

- `FATE Flow` 1.7版本后，开始支持多版本组件包同时存在，例如可以同时放入`1.7.0`和`1.7.1`版本的`fate`算法组件包
- 我们将算法组件包的提供者称为`组件提供者`，`名称`和`版本`唯一确定`组件提供者`
- 在提交作业时，可通过`job dsl`指定本次作业使用哪个组件包，具体请参考[组件provider](./fate_flow_job_scheduling.zh.md#35-组件provider)

## 2. 默认组件提供者

部署`FATE`集群将包含一个默认的组件提供者，其通常在 `${FATE_PROJECT_BASE}/python/federatedml` 目录下

## 3. 当前组件提供者

{{snippet('cli/provider.zh.md', '### list')}}

## 4. 新组件提供者

{{snippet('cli/provider.zh.md', '### register')}}