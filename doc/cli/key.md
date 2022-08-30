## Key

### query

Query the public key information of our or partner's fate site

```bash
flow key query -p 9999
```
**Options** 

| parameters | short-format | long-format | required | type | description |
| :-------- | :-----| :-----| :-----| :-----| -------------- |
| party_id | `-p` | `--party-id` | yes | string | site id |

**returns**

| parameter name | type | description |
| :------ | :----- | -------- |
| retcode | int | return-code |
| retmsg | string | return information |
| data | object | return data |

Sample

```json
{
  "data": "-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAzxgbxa3cfhvwbu0AFfY/\ nkm7uFZ17J0EEDgaIWlrLakds7XboU5iOT0eReQp/KG3R0fVM9rBtdj8NcBcArtZ9\n2242Atls3jiuza/MPPo9XACnedGW7O+ VAfvVmq2sdmKZMX5l7krEXYN645UZAd8b\nhIh+xf0qGW6IgxyKvqF13VxxB7OMUzUwyY/ZcN2rW1urfdXsCNoQ1cFl3KaarkHl\nn/ gBMcCDvACXoKysFnFE7L4E7CGglYaDBJrfIyti+sbSVNxUDx2at2VXqj/PohTa\nkBKfrgK7sT85gz1sc9uRwhwF4nOY7izq367S7t/W8BJ75gWsr+lhhiIfE19RBbBQ\n /wIDAQAB\n-----END PUBLIC KEY-----",
  "retcode": 0,
  "retmsg": "success"
}
```

### save

Used to save other fate site public key information, that is, for cooperation with other sites

```bash
flow key save -c fateflow/examples/key/save_public_key.json
```

**Options** 

| parameters | short format | long format | required | type | description |
| :-------- | :-----| :-----| :-----| :----- | -------------- |
| conf_path | `-c` | `-conf-path` | yes | string | configuration-path |

Note: conf_path is the parameter path, the specific parameters are as follows

| parameter name | required | type | description |
|:---------------| :--- | :----- |---------------------------------|
| party_id | yes | string | site id |
| key | yes | string | site public key |

**return**

| parameter name | type | description |
| :------ | :----- | -------- |
| retcode | int | return code |
| retmsg | string | return message |


Sample

```json
{
    "retcode": 0,
    "retmsg": "success"
}
```

### delete

Delete the partner site public key, i.e. cancel the partnership

```bash
flow key delete -p 9999
```

**Options** 

| parameters | short-format | long-format | required | type | description |
| :------ | :----- | :-----| :-----| :-----| -------- |
| party_id | `-p` | `--party-id` | yes | string | site id |

**returns**

| parameter name | type | description |
| :------ | :----- | -------- |
| retcode | int | return-code |
| retmsg | string | return message |


Sample

```json
{
    "retcode": 0,
    "retmsg": "success"
}
```