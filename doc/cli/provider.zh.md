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
            "1.9.0": {
                "class_path": {
                    "anonymous_generator": "util.anonymous_generator_util.Anonymous",
                    "data_format": "util.data_format_preprocess.DataFormatPreProcess",
                    "feature_instance": "feature.instance.Instance",
                    "feature_vector": "feature.sparse_vector.SparseVector",
                    "hetero_model_merge": "protobuf.model_merge.merge_hetero_models.hetero_model_merge",
                    "homo_model_convert": "protobuf.homo_model_convert.homo_model_convert",
                    "interface": "components.components.Components",
                    "model": "protobuf.generated",
                    "model_migrate": "protobuf.model_migrate.model_migrate"
                },
                "components": [
                    "heterodatasplit",
                    "psi",
                    "heterofastsecureboost",
                    "heterofeaturebinning",
                    "scorecard",
                    "sampleweight",
                    "homosecureboost",
                    "onehotencoder",
                    "secureinformationretrieval",
                    "homoonehotencoder",
                    "datatransform",
                    "dataio",
                    "heterosshelinr",
                    "intersection",
                    "homofeaturebinning",
                    "secureaddexample",
                    "union",
                    "datastatistics",
                    "columnexpand",
                    "homonn",
                    "labeltransform",
                    "heterosecureboost",
                    "heterofeatureselection",
                    "heterolr",
                    "feldmanverifiablesum",
                    "heteropoisson",
                    "evaluation",
                    "federatedsample",
                    "homodatasplit",
                    "ftl",
                    "localbaseline",
                    "featurescale",
                    "featureimputation",
                    "heteropearson",
                    "heterokmeans",
                    "heteronn",
                    "heterolinr",
                    "spdztest",
                    "heterosshelr",
                    "homolr"
                ],
                "path": "${FATE_PROJECT_BASE}/python/federatedml",
                "python": ""
            },
            "default": {
                "version": "1.9.0"
            }
        },
        "fate_flow": {
            "1.9.0": {
                "class_path": {
                    "anonymous_generator": "util.anonymous_generator_util.Anonymous",
                    "data_format": "util.data_format_preprocess.DataFormatPreProcess",
                    "feature_instance": "feature.instance.Instance",
                    "feature_vector": "feature.sparse_vector.SparseVector",
                    "hetero_model_merge": "protobuf.model_merge.merge_hetero_models.hetero_model_merge",
                    "homo_model_convert": "protobuf.homo_model_convert.homo_model_convert",
                    "interface": "components.components.Components",
                    "model": "protobuf.generated",
                    "model_migrate": "protobuf.model_migrate.model_migrate"
                },
                "components": [
                    "writer",
                    "modelrestore",
                    "upload",
                    "apireader",
                    "modelstore",
                    "cacheloader",
                    "modelloader",
                    "download",
                    "reader"
                ],
                "path": "${FATE_FLOW_BASE}/python/fate_flow",
                "python": ""
            },
            "default": {
                "version": "1.9.0"
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
    "data": {
        "flow-xxx-9380": {
            "retcode": 0,
            "retmsg": "success"
        }
    },
    "retcode": 0,
    "retmsg": "success"
}

```
