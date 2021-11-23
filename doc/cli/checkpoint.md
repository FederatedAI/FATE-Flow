## Checkpoint

### list

List checkpoints.

```bash
flow checkpoint list --model-id <model_id> --model-version <model_version> --role <role> --party-id <party_id> --component-name <component_name>
```

**Options**

| Parameter      | Short Flag | Long Flag          | Optional | Description    |
| -------------- | ---------- | ------------------ | -------- | -------------- |
| model_id       |            | `--model-id`       | No       | Model ID       |
| model_version  |            | `--model-version`  | No       | Model version  |
| role           | `-r`       | `--role`           | No       | Party role     |
| party_id       | `-p`       | `--party-id`       | No       | Party ID       |
| component_name | `-cpn`     | `--component-name` | No       | Component name |

**Example**

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

Get checkpoint information.

```bash
flow checkpoint get --model-id <model_id> --model-version <model_version> --role <role> --party-id <party_id> --component-name <component_name> --step-index <step_index>
```


**Example**

| Parameter      | Short Flag | Long Flag          | Optional | Description                                 |
| -------------- | ---------- | ------------------ | -------- | ------------------------------------------- |
| model_id       |            | `--model-id`       | No       | Model ID                                    |
| model_version  |            | `--model-version`  | No       | Model version                               |
| role           | `-r`       | `--role`           | No       | Party role                                  |
| party_id       | `-p`       | `--party-id`       | No       | Party ID                                    |
| component_name | `-cpn`     | `--component-name` | No       | Component name                              |
| step_index     |            | `--step-index`     | Yes      | Step index, cannot be used with `step_name` |
| step_name      |            | `--step-name`      | Yes      | Step name, cannot be used with `step_index` |

**Example**

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
