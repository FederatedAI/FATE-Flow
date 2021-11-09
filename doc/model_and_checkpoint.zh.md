# Pipeline 模型和 Checkpoint 模型

每个组件运行完成后保存的模型称为 Pipeline 模型，在组件运行时定时保存的模型称为 Checkpoint 模型。Checkpoint 模型也可以用于组件运行意外中断后，重试时的“断点续传”。

Pipeline 模型存储于 `model_local_cache/<party_model_id>/<model_version>/variables/data/<component_name>/<model_alias>`，Checkpoint 模型存储于 `model_local_cache/<party_model_id>/<model_version>/checkpoint/<component_name>/<step_index>#<step_name>`。

Checkpoint 模型的支持自 1.7.0 加入，默认是不保存的，如需启用，则要向 DSL 中加入 callback `ModelCheckpoint`。

## Model 相关接口

### `load`

向 Fate-Serving 加载 `deploy` 生成的模型。

| 参数      | 短格式 | 长格式        | 可选参数 | 说明     |
| --------- | ------ | ------------- | -------- | -------- |
| conf_path | `-c`   | `--conf-path` | 否       | 配置文件 |
| job_id    | `-j`   | `--job-id`    | 是       | 任务 ID  |

```bash
flow model load -c examples/model/publish_load_model.json
flow model load -c examples/model/publish_load_model.json -j <job_id>
```

### `bind`

向 Fate-Serving 绑定 `deploy` 生成的模型。

| 参数      | 短格式 | 长格式        | 可选参数 | 说明     |
| --------- | ------ | ------------- | -------- | -------- |
| conf_path | `-c`   | `--conf-path` | 否       | 配置文件 |
| job_id    | `-j`   | `--job-id`    | 是       | 任务 ID  |

```bash
flow model bind -c examples/model/bind_model_service.json
flow model bind -c examples/model/bind_model_service.json -j <job_id>
```

### `import`

从本地或存储引擎中导入模型。

| 参数          | 短格式 | 长格式            | 可选参数 | 说明                             |
| ------------- | ------ | ----------------- | -------- | -------------------------------- |
| conf_path     | `-c`   | `--conf-path`     | 否       | 配置文件                         |
| from_database |        | `--from-database` | 是       | 从 Flow 配置的存储引擎中导入模型 |

  - *示例*：

```bash
flow model import -c examples/model/import_model.json
flow model import -c examples/model/restore_model.json --from-database
```

### `export`

导出模型到本地或存储引擎中。

| 参数        | 短格式 | 长格式          | 可选参数 | 说明                               |
| ----------- | ------ | --------------- | -------- | ---------------------------------- |
| conf_path   | `-c`   | `--conf-path`   | 否       | 配置文件                           |
| to_database |        | `--to-database` | 是       | 将模型导出到 Flow 配置的存储引擎中 |

  - *示例*：

```bash
flow model export -c examples/model/export_model.json
flow model export -c examplse/model/store_model.json --to-database
```

### `migrate`

迁移模型。

| 参数      | 短格式 | 长格式        | 可选参数 | 说明     |
| --------- | ------ | ------------- | -------- | -------- |
| conf_path | `-c`   | `--conf-path` | 否       | 配置文件 |

  - *示例*：

```bash
flow model migrate -c examples/model/migrate_model.json
```

### `tag-list`

获取模型的标签列表。

| 参数   | 短格式 | 长格式     | 可选参数 | 说明    |
| ------ | ------ | ---------- | -------- | ------- |
| job_id | `-j`   | `--job_id` | 否       | 任务 ID |

``` bash
flow model tag-list -j <job_id>
```

### `tag-model`

向模型添加标签。

| 参数     | 短格式 | 长格式       | 可选参数 | 说明           |
| -------- | ------ | ------------ | -------- | -------------- |
| job_id   | `-j`   | `--job_id`   | 否       | 任务 ID        |
| tag_name | `-t`   | `--tag-name` | 否       | 标签名         |
| remove   |        | `--remove`   | 是       | 移除指定的标签 |

```bash
flow model tag-model -j <job_id> -t <tag_name>
flow model tag-model -j <job_id> -t <tag_name> --remove
```

### `deploy`

配置预测 DSL。

| 参数           | 短格式 | 长格式             | 可选参数 | 说明                                                         |
| -------------- | ------ | ------------------ | -------- | ------------------------------------------------------------ |
| model_id       |        | `--model-id`       | 否       | 模型 ID                                                      |
| model_version  |        | `--model-version`  | 否       | 模型版本                                                     |
| cpn_list       |        | `--cpn-list`       | 是       | 组件列表                                                     |
| cpn_path       |        | `--cpn-path`       | 是       | 从文件中读入组件列表                                         |
| dsl_path       |        | `--dsl-path`       | 是       | 预测 DSL 文件                                                |
| cpn_step_index |        | `--cpn-step-index` | 是       | 用指定的 Checkpoint 模型替换 Pipeline 模型<br />使用 `:` 分隔 component name 与 step index<br />例如 `--cpn-step-index cpn_a:123` |
| cpn_step_name  |        | `--cpn-step-name`  | 是       | 用指定的 Checkpoint 模型替换 Pipeline 模型<br />使用 `:` 分隔 component name 与 step name<br />例如 `--cpn-step-name cpn_b:foobar` |

```bash
flow model deploy --model-id <model_id> --model-version <model_version>
```

### `get-predict-dsl`

 获取预测 DSL。

| 参数          | 短格式 | 长格式            | 可选参数 | 说明     |
| ------------- | ------ | ----------------- | -------- | -------- |
| model_id      |        | `--model-id`      | 否       | 模型 ID  |
| model_version |        | `--model-version` | 否       | 模型版本 |
| output_path   | `-o`   | `--output-path`   | 否       | 输出路径 |

```bash
flow model get-predict-dsl --model-id <model_id> --model-version <model_version> -o ./examples/
```

### `get-predict-conf`

模型预测模板。

| 参数          | 短格式 | 长格式            | 可选参数 | 说明     |
| ------------- | ------ | ----------------- | -------- | -------- |
| model_id      |        | `--model-id`      | 否       | 模型 ID  |
| model_version |        | `--model-version` | 否       | 模型版本 |
| output_path   | `-o`   | `--output-path`   | 否       | 输出路径 |

```bash
flow model get-predict-conf --model-id <model_id> --model-version <model_version> -o ./examples/
```

### `get-model-info`

获取模型信息。

| 参数          | 短格式 | 长格式            | 可选参数 | 说明         |
| ------------- | ------ | ----------------- | -------- | ------------ |
| model_id      |        | `--model-id`      | 否       | 模型 ID      |
| model_version |        | `--model-version` | 否       | 模型版本     |
| role          | `-r`   | `--role`          | 是       | Party 角色   |
| party_id      | `-p`   | `--party-id`      | 是       | Party ID     |
| detail        |        | `--detail`        | 是       | 展示详细信息 |

```bash
flow model get-model-info --model-id <model_id> --model-version <model_version>
flow model get-model-info --model-id <model_id> --model-version <model_version> --detail
```

### `homo-convert`

基于横向训练的模型，生成其他 ML  框架的模型文件。

| 参数      | 短格式 | 长格式        | 可选参数 | 说明     |
| --------- | ------ | ------------- | -------- | -------- |
| conf_path | `-c`   | `--conf-path` | 否       | 配置文件 |

```bash
flow model homo-convert -c examples/model/homo_convert_model.json
```

### `homo-deploy`

将横向训练后使用 `homo-convert` 生成的模型部署到在线推理系统中，当前支持创建基于 KFServing 的推理服务。

| 参数      | 短格式 | 长格式        | 可选参数 | 说明             |
| --------- | ------ | ------------- | -------- | ---------------- |
| conf_path | `-c`   | `--conf-path` | 否       | 任务配置文件路径 |

```bash
flow model homo-deploy -c examples/model/homo_deploy_model.json
```

## Checkpoint 相关接口

### `list`

获取 Checkpoint 模型列表。

| 参数           | 短格式 | 长格式             | 可选参数 | 说明       |
| -------------- | ------ | ------------------ | -------- | ---------- |
| model_id       |        | `--model-id`       | 否       | 模型 ID    |
| model_version  |        | `--model-version`  | 否       | 模型版本   |
| role           | `-r`   | `--role`           | 否       | Party 角色 |
| party_id       | `-p`   | `--party-id`       | 否       | Party ID   |
| component_name | `-cpn` | `--component-name` | 否       | 组件名     |

```bash
flow checkpoint list --model-id <model_id> --model-version <model_version> --role <role> --party-id <party_id> --component-name <component_name>
```

### `get`

获取 Checkpoint 模型信息。

| 参数           | 短格式 | 长格式             | 可选参数 | 说明                                  |
| -------------- | ------ | ------------------ | -------- | ------------------------------------- |
| model_id       |        | `--model-id`       | 否       | 模型 ID                               |
| model_version  |        | `--model-version`  | 否       | 模型版本                              |
| role           | `-r`   | `--role`           | 否       | Party 角色                            |
| party_id       | `-p`   | `--party-id`       | 否       | Party ID                              |
| component_name | `-cpn` | `--component-name` | 否       | 组件名                                |
| step_index     |        | `--step-index`     | 是       | Step index，不可与 step_name 同时使用 |
| step_name      |        | `--step-name`      | 是       | Step name，不可与 step_index 同时使用 |

```bash
flow checkpoint get --model-id <model_id> --model-version <model_version> --role <role> --party-id <party_id> --component-name <component_name> --step-index <step_index>
```
