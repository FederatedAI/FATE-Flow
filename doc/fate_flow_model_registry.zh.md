# 联合模型注册中心

## 1. 说明

由 FATE 训练的模型会自动保存到本地并记录在 FATE-Flow 的数据库中，每个组件运行完成后保存的模型称为 Pipeline 模型，在组件运行时定时保存的模型称为 Checkpoint 模型。Checkpoint 模型也可以用于组件运行意外中断后，重试时的“断点续传”。

Checkpoint 模型的支持自 1.7.0 加入，默认是不保存的，如需启用，则要向 DSL 中加入 callback `ModelCheckpoint`。

### 本地磁盘存储

- Pipeline 模型存储于 `model_local_cache/<party_model_id>/<model_version>/variables/data/<component_name>/<model_alias>`。

- Checkpoint 模型存储于 `model_local_cache/<party_model_id>/<model_version>/checkpoint/<component_name>/<step_index>#<step_name>`。

#### 目录结构

```
tree model_local_cache/guest#9999#arbiter-10000#guest-9999#host-10000#model/202112181502241234200

model_local_cache/guest#9999#arbiter-10000#guest-9999#host-10000#model/202112181502241234200
├── checkpoint
│   ├── data_transform_0
│   ├── evaluation_0
│   ├── hetero_linr_0
│   │   ├── 0#step_name
│   │   │   ├── HeteroLinearRegressionMeta.json
│   │   │   ├── HeteroLinearRegressionMeta.pb
│   │   │   ├── HeteroLinearRegressionParam.json
│   │   │   ├── HeteroLinearRegressionParam.pb
│   │   │   └── database.yaml
│   │   ├── 1#step_name
│   │   │   ├── HeteroLinearRegressionMeta.json
│   │   │   ├── HeteroLinearRegressionMeta.pb
│   │   │   ├── HeteroLinearRegressionParam.json
│   │   │   ├── HeteroLinearRegressionParam.pb
│   │   │   └── database.yaml
│   │   ├── 2#step_name
│   │   │   ├── HeteroLinearRegressionMeta.json
│   │   │   ├── HeteroLinearRegressionMeta.pb
│   │   │   ├── HeteroLinearRegressionParam.json
│   │   │   ├── HeteroLinearRegressionParam.pb
│   │   │   └── database.yaml
│   │   ├── 3#step_name
│   │   │   ├── HeteroLinearRegressionMeta.json
│   │   │   ├── HeteroLinearRegressionMeta.pb
│   │   │   ├── HeteroLinearRegressionParam.json
│   │   │   ├── HeteroLinearRegressionParam.pb
│   │   │   └── database.yaml
│   │   └── 4#step_name
│   │       ├── HeteroLinearRegressionMeta.json
│   │       ├── HeteroLinearRegressionMeta.pb
│   │       ├── HeteroLinearRegressionParam.json
│   │       ├── HeteroLinearRegressionParam.pb
│   │       └── database.yaml
│   ├── hetero_linr_1
│   ├── intersection_0
│   └── reader_0
├── define
│   ├── define_meta.yaml
│   ├── proto
│   │   └── pipeline.proto
│   └── proto_generated_python
│       ├── __pycache__
│       │   └── pipeline_pb2.cpython-36.pyc
│       └── pipeline_pb2.py
├── run_parameters
│   ├── data_transform_0
│   │   └── run_parameters.json
│   ├── hetero_linr_0
│   │   └── run_parameters.json
│   ├── hetero_linr_1
│   │   └── run_parameters.json
│   └── pipeline
│       └── run_parameters.json
└── variables
    ├── data
    │   ├── data_transform_0
    │   │   └── model
    │   │       ├── DataTransformMeta
    │   │       ├── DataTransformMeta.json
    │   │       ├── DataTransformParam
    │   │       └── DataTransformParam.json
    │   ├── hetero_linr_0
    │   │   └── model
    │   │       ├── HeteroLinearRegressionMeta
    │   │       ├── HeteroLinearRegressionMeta.json
    │   │       ├── HeteroLinearRegressionParam
    │   │       └── HeteroLinearRegressionParam.json
    │   ├── hetero_linr_1
    │   │   └── model
    │   │       ├── HeteroLinearRegressionMeta
    │   │       ├── HeteroLinearRegressionMeta.json
    │   │       ├── HeteroLinearRegressionParam
    │   │       └── HeteroLinearRegressionParam.json
    │   └── pipeline
    │       └── pipeline
    │           ├── Pipeline
    │           └── Pipeline.json
    └── index

32 directories, 47 files
```

**`checkpoint`**

此目录存储组件运行过程中，每轮迭代产生的模型，不是所有组件都支持 checkpoint。

以 `checkpoint/hetero_linr_0/2#step_name` 为例：

`hetero_linr_0` 是 `component_name`；`2` 是 `step_index`，即迭代次数；`step_name` 目前只做占位符，没有使用。

`HeteroLinearRegressionMeta.json`, `HeteroLinearRegressionMeta.pb`, `HeteroLinearRegressionParam.json`, `HeteroLinearRegressionParam.pb` 都是训练产生的数据，可以理解为模型文件。`database.yaml` 主要记录上述文件的 hash 以作校验，还存储有 `step_index`, `step_name`, `create_time`。

**`define`**

该目录储存作业的基本信息，在作业初始化时创建。`pipeline` 不是一个组件，而是代表整个作业。

`define/proto/pipeline.proto` 和 `define/proto/pipeline_pb2.py` 目前没有使用。

`define/define_meta.yaml` 记录组件列表，包括 `component_name`, `componet_module_name`, `model_alias`。

**`run_parameters`**

此目录存储组件的配置信息，也称为 DSL。

`run_parameters/pipeline/run_parameters.json` 为一个空的 object `{}`。

**`variables`**

此目录存储组件运行结束后产生的模型，与最后一轮迭代产生的模型一致。

以 `variables/data/hetero_linr_0/model` 为例：

`hetero_linr_0` 是 `component_name`；`model` 是 `model_alias`。

`HeteroLinearRegressionMeta`, `HeteroLinearRegressionMeta.json`, `HeteroLinearRegressionParam` `HeteroLinearRegressionParam.json` 与 `checkpoint` 目录下的文件格式完全一致，除了 `.pb` 文件去掉了扩展名。

`variables/data/pipeline/`存储作业的详细信息。

`variables/index/` 目前没有使用。

### 远端存储引擎

本地磁盘并不可靠，因此模型有丢失的风险，FATE-Flow 支持导出模型到指定存储引擎、从指定存储引擎导入以及自动发布模型时推送模型到引擎存储。

存储引擎支持腾讯云对象存储、MySQL 和 Redis, 具体请参考[存储引擎配置](#4-存储引擎配置)

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
