# FATE Flow 任务组件注册中心

[TOC]

## 1. 说明

- `FATE Flow` 1.7版本后，开始支持多版本组件包同时存在，例如可以同时放入`1.7.0`和`1.7.1`版本的`fate`算法组件包
- 我们将算法组件包的提供者称为`组件提供者`，`名称`和`版本`唯一确定`组件提供者`
- 在提交作业时，可通过`job dsl`指定本次作业使用哪个组件包，具体请参考[组件provider](./fate_flow_job_scheduling.zh.md#35-组件provider)

## 2. 默认组件提供者

部署`FATE`集群将包含一个默认的组件提供者，其通常在 `${FATE_PROJECT_BASE}/python/federatedml` 目录下

## 3. 列出当前组件提供者

**请求CLI** 

```bash
flow provider list
```

**请求参数** 

**返回参数** 

| 参数名  | 类型   | 说明     |
| :------ | :----- | -------- |
| retcode | int    | 返回码   |
| retmsg  | string | 返回信息 |
| data    | dict   | 返回数据 |

**样例** 

输出:

```json
{
    "data": {
        "fate": {
            "1.7.0": {
                "class_path": {
                    "feature_instance": "feature.instance.Instance",
                    "feature_vector": "feature.sparse_vector.SparseVector",
                    "homo_model_convert": "protobuf.homo_model_convert.homo_model_convert",
                    "interface": "components.components.Components",
                    "model": "protobuf.generated",
                    "model_migrate": "protobuf.model_migrate.model_migrate"
                },
                "components": [
                    "heterolinr",
                    "homoonehotencoder",
                    "dataio",
                    "psi",
                    "homodatasplit",
                    "homolr",
                    "columnexpand",
                    "heterokmeans",
                    "heterosshelr",
                    "homosecureboost",
                    "heteropoisson",
                    "featureimputation",
                    "heterofeatureselection",
                    "heteropearson",
                    "heterodatasplit",
                    "ftl",
                    "heterolr",
                    "homonn",
                    "evaluation",
                    "featurescale",
                    "intersection",
                    "heteronn",
                    "datastatistics",
                    "heterosecureboost",
                    "sbtfeaturetransformer",
                    "datatransform",
                    "heterofeaturebinning",
                    "feldmanverifiablesum",
                    "heterofastsecureboost",
                    "federatedsample",
                    "secureaddexample",
                    "secureinformationretrieval",
                    "sampleweight",
                    "union",
                    "onehotencoder",
                    "homofeaturebinning",
                    "scorecard",
                    "localbaseline",
                    "labeltransform"
                ],
                "path": "${FATE_PROJECT_BASE}/python/federatedml",
                "python": ""
            },
            "default": {
                "version": "1.7.0"
            }
        },
        "fate_flow": {
            "1.7.0": {
                "class_path": {
                    "feature_instance": "feature.instance.Instance",
                    "feature_vector": "feature.sparse_vector.SparseVector",
                    "homo_model_convert": "protobuf.homo_model_convert.homo_model_convert",
                    "interface": "components.components.Components",
                    "model": "protobuf.generated",
                    "model_migrate": "protobuf.model_migrate.model_migrate"
                },
                "components": [
                    "download",
                    "upload",
                    "modelloader",
                    "reader",
                    "modelrestore",
                    "cacheloader",
                    "modelstore"
                ],
                "path": "${FATE_FLOW_BASE}/python/fate_flow",
                "python": ""
            },
            "default": {
                "version": "1.7.0"
            }
        }
    },
    "retcode": 0,
    "retmsg": "success"
}
```

包含`组件提供者`的`名称`, `版本号`, `代码路径`, `提供的组件列表`

## 4. 注册一个组件提供者

**请求CLI** 

```bash
flow provider register -c $FATE_FLOW_BASE/examples/other/register_provider.json
```

**请求参数** 

| 参数名                 | 必选 | 类型   | 说明                             |
| :--------------------- | :--- | :----- | ------------------------------|
| -c, --conf-path          | 是   | string | 配置路径                         |

**返回参数** 

| 参数名  | 类型   | 说明     |
| :------ | :----- | -------- |
| retcode | int    | 返回码   |
| retmsg  | string | 返回信息 |

**样例** 

```bash
flow provider register -c $FATE_FLOW_BASE/examples/other/register_provider.json
```

配置文件：

```json
{
  "name": "fate",
  "version": "1.7.1",
  "path": "${FATE_FLOW_BASE}/python/component_plugins/fateb/python/federatedml"
}
```

输出:

```json
{
    "retcode": 0,
    "retmsg": "success"
}
```
