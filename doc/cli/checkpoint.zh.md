## Checkpoint

### list

获取 Checkpoint 模型列表。

```bash
flow checkpoint list --model-id <model_id> --model-version <model_version> --role <role> --party-id <party_id> --component-name <component_name>
```

**选项**

| 参数           | 短格式 | 长格式             | 可选参数 | 说明       |
| -------------- | ------ | ------------------ | -------- | ---------- |
| model_id       |        | `--model-id`       | 否       | 模型 ID    |
| model_version  |        | `--model-version`  | 否       | 模型版本   |
| role           | `-r`   | `--role`           | 否       | Party 角色 |
| party_id       | `-p`   | `--party-id`       | 否       | Party ID   |
| component_name | `-cpn` | `--component-name` | 否       | 组件名     |

**样例**

```json
{
  "retcode": 0,
  "retmsg": "success",
  "data": [
    {
      "create_time": "2021-11-07T02:34:54.683015",
      "step_index": 0,
      "step_name": "step_name",
      "models": {
        "HeteroLogisticRegressionMeta": {
          "buffer_name": "LRModelMeta",
          "sha1": "6871508f6e6228341b18031b3623f99a53a87147"
        },
        "HeteroLogisticRegressionParam": {
          "buffer_name": "LRModelParam",
          "sha1": "e3cb636fc93675684bff27117943f5bfa87f3029"
        }
      }
    }
  ]
}
```

### get

获取 Checkpoint 模型信息。

```bash
flow checkpoint get --model-id <model_id> --model-version <model_version> --role <role> --party-id <party_id> --component-name <component_name> --step-index <step_index>
```


**选项**

| 参数           | 短格式 | 长格式             | 可选参数 | 说明                                  |
| -------------- | ------ | ------------------ | -------- | ------------------------------------- |
| model_id       |        | `--model-id`       | 否       | 模型 ID                               |
| model_version  |        | `--model-version`  | 否       | 模型版本                              |
| role           | `-r`   | `--role`           | 否       | Party 角色                            |
| party_id       | `-p`   | `--party-id`       | 否       | Party ID                              |
| component_name | `-cpn` | `--component-name` | 否       | 组件名                                |
| step_index     |        | `--step-index`     | 是       | Step index，不可与 step_name 同时使用 |
| step_name      |        | `--step-name`      | 是       | Step name，不可与 step_index 同时使用 |

**样例**

```json
{
  "retcode": 0,
  "retmsg": "success",
  "data": {
    "create_time": "2021-11-07T02:34:54.683015",
    "step_index": 0,
    "step_name": "step_name",
    "models": {
      "HeteroLogisticRegressionMeta": "CgJMMhEtQxzr4jYaPxkAAAAAAADwPyIHcm1zcHJvcDD///////////8BOTMzMzMzM8M/QApKBGRpZmZYAQ==",
      "HeteroLogisticRegressionParam": "Ig0KAng3EW1qASu+uuO/Ig0KAng0EcNi7a65ReG/Ig0KAng4EbJbl4gvVea/Ig0KAng2EcZwlVZTkOu/Ig0KAngwEVpG8dCbGvG/Ig0KAng5ESJNTx5MLve/Ig0KAngzEZ88H9P8qfO/Ig0KAng1EVfWP8JJv/K/Ig0KAngxEVS0xVXoTem/Ig0KAngyEaApgW32Q/K/KSiiE8AukPs/MgJ4MDICeDEyAngyMgJ4MzICeDQyAng1MgJ4NjICeDcyAng4MgJ4OUj///////////8B"
    }
  }
}
```
