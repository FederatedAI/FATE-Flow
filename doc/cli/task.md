## Task

### query

Retrieve Task information

**Options**

| number | parameters | short format | long format | required parameters | parameter description |
| ---- | -------------- | ------ | ------------------ | -------- | -------- |
| 1 | job_id | `-j` | `--job_id` | no | Job ID |
| 2 | role | `-r` | `--role` | no | role
| 3 | party_id | `-p` | `--party_id` | no | Party ID |
| 4 | component_name | `-cpn` | `--component_name` | no | component_name |
| 5 | status | `-s` | `--status` | No | Task status |

**Example**

``` bash
flow task query -j $JOB_ID -p 9999 -r guest
flow task query -cpn hetero_feature_binning_0 -s complete
```

### list

Show the list of Tasks.
**Options**

| number | parameters | short format | long format | required parameters | parameter description |
| ---- | ----- | ------ | --------- | -------- | ---------------------------- |
| 1 | limit | `-l` | `-limit` | no | Returns a limit on the number of results (default: 10) |

**Example**

``` bash
flow task list
flow task list -l 25
```
