# 联合模型注册中心

## 1. 说明

由 FATE 训练的模型会自动保存到本地并记录在 FATE-Flow 的数据库中，每个组件运行完成后保存的模型称为 Pipeline 模型，在组件运行时定时保存的模型称为 Checkpoint 模型。Checkpoint 模型也可以用于组件运行意外中断后，重试时的“断点续传”。

Checkpoint 模型的支持自 1.7.0 加入，默认是不保存的，如需启用，则要向 DSL 中加入 callback `ModelCheckpoint`。

### 本地磁盘存储

- Pipeline 模型存储于 `model_local_cache/<party_model_id>/<model_version>/variables/data/<component_name>/<model_alias>`。

- Checkpoint 模型存储于 `model_local_cache/<party_model_id>/<model_version>/checkpoint/<component_name>/<step_index>#<step_name>`。

### 远端存储引擎

本地磁盘并不可靠，因此模型有丢失的风险，FATE-Flow 支持导出模型到指定存储引擎、从指定存储引擎导入以及自动发布模型时推送模型到引擎存储。

存储引擎支持腾讯云对象存储、MySQL 和 Redis, 具体请参考[存储引擎配置](#5-存储引擎配置)

## 2. Model

{{snippet('cli/model.zh.md', '## Model')}}

## 3. Checkpoint

{{snippet('cli/checkpoint.zh.md', '## Checkpoint')}}

## 4. 存储引擎配置

### `enable_model_store`

开启后，在调用 `/model/load` 时：如果模型文件在本地磁盘存在、但不在存储引擎中，则自动把模型文件上传至存储引擎；如果模型文件在存储引擎存在、但不在本地磁盘中，则自动把模型文件下载到本地磁盘。

此配置不影响 `/model/store` 和 `/model/restore`。

### `model_store_address`

此配置定义使用的存储引擎。

#### 腾讯云对象存储

```yaml
storage: tencent_cos
# 请从腾讯云控制台获取下列配置
Region:
SecretId:
SecretKey:
Bucket:
```

#### MySQL

```yaml
storage: mysql
database: fate_model
user: fate
password: fate
host: 127.0.0.1
port: 3306
# 可选的数据库连接参数
max_connections: 10
stale_timeout: 10
```

#### Redis

```yaml
storage: redis
host: 127.0.0.1
port: 6379
db: 0
password:
# key 的超时时间，单位秒。默认 None，没有超时时间。
ex:
```
