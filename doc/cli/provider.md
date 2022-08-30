## Provider

### list

List all current component providers and information about the components they provide

```bash
flow provider list [options]
```

**Options**

**Returns**

| 参数名  | 类型   | 说明     |
| :------ | :----- | -------- |
| retcode | int    | 返回码   |
| retmsg  | string | 返回信息 |
| data    | dict   | 返回数据 |

**Example**

output:

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

Contains the `name`, `version number`, `codepath`, `list of provided components`

### register

Register a component provider

```bash
flow provider register [options]
```

**Options**

| 参数名                 | 必选 | 类型   | 说明                             |
| :--------------------- | :--- | :----- | ------------------------------|
| -c, --conf-path          | 是   | string | 配置路径                         |

**Returns**

| 参数名  | 类型   | 说明     |
| :------ | :----- | -------- |
| retcode | int    | 返回码   |
| retmsg  | string | 返回信息 |

**Example**

```bash
flow provider register -c $FATE_FLOW_BASE/examples/other/register_provider.json
```

conf:

```json
{
  "name": "fate",
  "version": "1.7.1",
  "path": "${FATE_FLOW_BASE}/python/component_plugins/fateb/python/federatedml"
}
```

output:

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
