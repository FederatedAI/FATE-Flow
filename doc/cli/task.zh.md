## Task

### query

检索Task信息

**选项**

| 编号 | 参数           | 短格式 | 长格式             | 必要参数 | 参数介绍 |
| ---- | -------------- | ------ | ------------------ | -------- | -------- |
| 1    | job_id         | `-j`   | `--job_id`         | 否       | Job ID   |
| 2    | role           | `-r`   | `--role`           | 否       | 角色     |
| 3    | party_id       | `-p`   | `--party_id`       | 否       | Party ID |
| 4    | component_name | `-cpn` | `--component_name` | 否       | 组件名   |
| 5    | status         | `-s`   | `--status`         | 否       | 任务状态 |

**样例**

``` bash
flow task query -j $JOB_ID -p 9999 -r guest
flow task query -cpn hetero_feature_binning_0 -s complete
```

### list

展示Task列表。
**选项**

| 编号 | 参数  | 短格式 | 长格式    | 必要参数 | 参数介绍                     |
| ---- | ----- | ------ | --------- | -------- | ---------------------------- |
| 1    | limit | `-l`   | `--limit` | 否       | 返回结果数量限制（默认：10） |

**样例**

``` bash
flow task list
flow task list -l 25
```
