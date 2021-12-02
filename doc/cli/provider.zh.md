## Provider

### list

列出当前所有组件提供者及其提供组件信息

```bash
flow provider list [options]
```

**选项**

**返回**

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

### register

注册一个组件提供者

```bash
flow provider register [options]
```

**选项**

| 参数名                 | 必选 | 类型   | 说明                             |
| :--------------------- | :--- | :----- | ------------------------------|
| -c, --conf-path          | 是   | string | 配置路径                         |

**返回**

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
