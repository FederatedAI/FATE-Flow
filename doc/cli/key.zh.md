## Key

### query

用于查询本方或合作方fate站点公钥信息

```bash
flow key query -p 9999
```
**选项** 

| 参数    | 短格式 | 长格式 | 必选 | 类型   | 说明           |
| :-------- | :--- | :--- | :--- | :----- | -------------- |
| party_id | `-p` | `--party-id` |是   | string | 站点id |

**返回**

| 参数名  | 类型   | 说明     |
| :------ | :----- | -------- |
| retcode | int    | 返回码   |
| retmsg  | string | 返回信息 |
| data    | object | 返回数据 |

样例

```json
{
  "data": "-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAzxgbxa3cfhvwbu0AFfY/\nkm7uFZ17J0EEDgaIWlrLakds7XboU5iOT0eReQp/KG3R0fVM9rBtdj8NcBcArtZ9\n2242Atls3jiuza/MPPo9XACnedGW7O+VAfvVmq2sdmKZMX5l7krEXYN645UZAd8b\nhIh+xf0qGW6IgxyKvqF13VxxB7OMUzUwyY/ZcN2rW1urfdXsCNoQ1cFl3KaarkHl\nn/gBMcCDvACXoKysFnFE7L4E7CGglYaDBJrfIyti+sbSVNxUDx2at2VXqj/PohTa\nkBKfrgK7sT85gz1sc9uRwhwF4nOY7izq367S7t/W8BJ75gWsr+lhhiIfE19RBbBQ\n/wIDAQAB\n-----END PUBLIC KEY-----",
  "retcode": 0,
  "retmsg": "success"
}
```

### save

用于保存其它fate站点公钥信息，即为和其他站点合作

```bash
flow key save -c fateflow/examples/key/save_public_key.json
```

**选项** 

| 参数    | 短格式 | 长格式 | 必选 | 类型   | 说明           |
| :-------- | :--- | :--- | :--- | :----- | -------------- |
| conf_path | `-c`   |`--conf-path`   |是   | string | 配置路径  |

注: conf_path为参数路径，具体参数如下

| 参数名            | 必选 | 类型   | 说明                              |
|:---------------| :--- | :----- |---------------------------------|
| party_id       | 是   | string | 站点id                            |
| key            | 是   | string | 站点公钥                            |

**返回**

| 参数名  | 类型   | 说明     |
| :------ | :----- | -------- |
| retcode | int    | 返回码   |
| retmsg  | string | 返回信息 |


样例

```json
{
    "retcode": 0,
    "retmsg": "success"
}
```

### delete

删除合作方站点公钥，即为取消合作关系

```bash
flow key delete -p 9999
```

**选项** 

| 参数    | 短格式 | 长格式 | 必选 | 类型   | 说明           |
| :-------- | :--- | :--- | :--- | :----- | -------------- |
| party_id | `-p` | `--party-id` |是   | string | 站点id |

**返回**

| 参数名  | 类型   | 说明     |
| :------ | :----- | -------- |
| retcode | int    | 返回码   |
| retmsg  | string | 返回信息 |


样例

```json
{
    "retcode": 0,
    "retmsg": "success"
}
```
