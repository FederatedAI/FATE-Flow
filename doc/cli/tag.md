## Tag

### create

Creates a label.

**Options**

| number | parameters | short-format | long-format | required parameters | parameter description |
| ---- | ------------ | ------ | ------------ | -------- | -------- |
| 1 | tag_name | `-t` | `-tag-name` | yes | tag_name |
| 2 | tag_parameter_introduction | `-d` | `--tag-desc` | no | tag_introduction |

**Example**

``` bash
flow tag create -t tag1 -d "This is the parameter description of tag1."
flow tag create -t tag2
```

### update

Update the tag information.

**Options**

| number | parameters | short format | long format | required parameters | parameter description |
| ---- | ------------ | ------ | ---------------- | -------- | ---------- |
| 1 | tag_name | `-t` | `--tag-name` | yes | tag_name |
| 2 | new_tag_name | | `--new-tag-name` | no | new-tag-name |
| 3 | new_tag_desc | | `--new-tag-desc` | no | new tag introduction |

**Example**

``` bash
flow tag update -t tag1 --new-tag-name tag2
flow tag update -t tag1 --new-tag-desc "This is the introduction of the new parameter."
```

### list

Show the list of tags.

**options**

| number | parameters | short-format | long-format | required-parameters | parameter-introduction |
| ---- | ----- | ------ | --------- | -------- | ---------------------------- |
| 1 | limit | `-l` | `-limit` | no | Returns a limit on the number of results (default: 10) |

**Example**

``` bash
flow tag list
flow tag list -l 3
```

### query

Retrieve tags.

**Options**

| number | parameters | short-format | long-format | required parameters | parameter description |
| ---- | ---------- | ------ | -------------- | -------- | -------------------------------------- |
| 1 | tag_name | `-t` | `-tag-name` | yes | tag_name |
| 2 | with_model | | `-with-model` | no | If specified, information about models with this tag will be displayed |

**Example**

``` bash
flow tag query -t $TAG_NAME
flow tag query -t $TAG_NAME --with-model
```

### delete

Delete the tag.

**Options**

| number | parameters | short-format | long-format | required-parameters | parameters introduction |
| ---- | -------- | ------ | ------------ | -------- | --------
| 1 | tag_name | `-t` | `---tag-name` | yes | tag_name |

**Example**

``` bash
flow tag delete -t tag1
```
