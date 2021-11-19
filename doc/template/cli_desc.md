**请求CLI** 

```bash
flow
```

**参数** 

| 参数名                 | 必选 | 类型   | 说明                             |
| :--------------------- | :--- | :----- | ------------------------------|
| -j, --job-id           | 是   | string | 作业id                         |
| -r, --role             | 是   | string | 参与角色                        |
| -p, --partyid          | 是   | string | 参与方id                        |
| -cpn, --component-name | 是   | string | 组件名，与job dsl中的保持一致      |
| -o, --output-path      | 是   | string | 输出数据的存放路径                |

**返回参数** 

| 参数名  | 类型   | 说明     |
| :------ | :----- | -------- |
| retcode | int    | 返回码   |
| retmsg  | string | 返回信息 |
| data    | dict   | 返回数据 |
| jobId   | string | 作业id   |

**样例** 

```bash
flow
```

输出:

```json
```
