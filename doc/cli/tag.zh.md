## Tag

### create

-   *介绍*： 创建标签。
-   *参数*：

| 编号 | 参数         | 短格式 | 长格式       | 必要参数 | 参数介绍 |
| ---- | ------------ | ------ | ------------ | -------- | -------- |
| 1    | tag_name     | `-t`   | `--tag-name` | 是       | 标签名   |
| 2    | tag_参数介绍 | `-d`   | `--tag-desc` | 否       | 标签介绍 |

-   *示例*：

``` bash
flow tag create -t tag1 -d "This is the 参数介绍 of tag1."
flow tag create -t tag2
```

### update

-   *介绍*： 更新标签信息。
-   *参数*：

| 编号 | 参数         | 短格式 | 长格式           | 必要参数 | 参数介绍   |
| ---- | ------------ | ------ | ---------------- | -------- | ---------- |
| 1    | tag_name     | `-t`   | `--tag-name`     | 是       | 标签名     |
| 2    | new_tag_name |        | `--new-tag-name` | 否       | 新标签名   |
| 3    | new_tag_desc |        | `--new-tag-desc` | 否       | 新标签介绍 |

-   *示例*：

``` bash
flow tag update -t tag1 --new-tag-name tag2
flow tag update -t tag1 --new-tag-desc "This is the new 参数介绍."
```

### list

-   *介绍*： 展示标签列表。
-   *参数*：

| 编号 | 参数  | 短格式 | 长格式    | 必要参数 | 参数介绍                     |
| ---- | ----- | ------ | --------- | -------- | ---------------------------- |
| 1    | limit | `-l`   | `--limit` | 否       | 返回结果数量限制（默认：10） |

-   *示例*：

``` bash
flow tag list
flow tag list -l 3
```

### query

-   *介绍*： 检索标签。
-   *参数*：

| 编号 | 参数       | 短格式 | 长格式         | 必要参数 | 参数介绍                               |
| ---- | ---------- | ------ | -------------- | -------- | -------------------------------------- |
| 1    | tag_name   | `-t`   | `--tag-name`   | 是       | 标签名                                 |
| 2    | with_model |        | `--with-model` | 否       | 如果指定，具有该标签的模型信息将被展示 |

-   *示例*：

``` bash
flow tag query -t $TAG_NAME
flow tag query -t $TAG_NAME --with-model
```

### delete

-   *介绍*： 删除标签。
-   *参数*：

| 编号 | 参数     | 短格式 | 长格式       | 必要参数 | 参数介绍 |
| ---- | -------- | ------ | ------------ | -------- | -------- |
| 1    | tag_name | `-t`   | `--tag-name` | 是       | 标签名   |

-   *示例*：

``` bash
flow tag delete -t tag1
```
