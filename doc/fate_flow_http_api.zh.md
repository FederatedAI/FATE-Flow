# REST API

## 1. 说明

## 2. 接口鉴权

Flow HTTP API 在 1.7.0 新增了签名鉴权，如果在配置文件里设置了 `http_app_key` 和 `http_secret_key`，则所有发送到 Flow 的请求都需要增加以下 header

`TIMESTAMP`：Unix timestamp，单位毫秒，如 `1634890066095` 表示 `2021-10-22 16:07:46 GMT+0800`，注意该时间与服务器当前时间的差距不能超过 60 秒

`NONCE`：随机字符串，可以使用 UUID，如 `782d733e-330f-11ec-8be9-a0369fa972af`

`APP_KEY`：需与 Flow 配置文件中的 `http_app_key` 一致

`SIGNATURE`：基于 Flow 配置文件中的 `http_secret_key` 和请求参数生成的签名

### 2.1 签名生成方法

- 按照顺序组合下列内容

`TIMESTAMP`

`NONCE`

`APP_KEY`

请求路径+查询参数，如没有查询参数则不需要末尾的 `?`，如 `/v1/job/submit` 或 `/v1/data/upload?table_name=dvisits_hetero_guest&namespace=experiment`

如果 `Content-Type` 为 `application/json`，则为原始 JSON，即 request body；如果不是，此项使用空字符串填充

如果 `Content-Type` 为 `application/x-www-form-urlencoded` 或 `multipart/form-data`，则需要把所有参数以字母顺序排序并 `urlencode`，转码方式参照 RFC 3986（即除 `a-zA-Z0-9-._~` 以外的字符都要转码），注意文件不参与签名；如果不是，此项使用空字符串填充

- 把所有参数用换行符 `\n` 连接然后以 `ASCII` 编码

- 使用 `HMAC-SHA1` 算法，以 Flow 配置文件中的 `http_secret_key` 为密钥，算出二进制摘要

- 使用 base64 编码二进制摘要

### 2.2. 示例

可以参考 [Fate SDK](https://github.com/FederatedAI/FATE/blob/develop-1.7/python/fate_client/flow_sdk/client/base.py#L63) 的签名方法或 [Fate Flow](https://github.com/FederatedAI/FATE-Flow/blob/develop-1.7.0/python/fate_flow/apps/__init__.py#L104) 的校验方法

### 2.3. 错误码

`400 Bad Request` request body 既有 json 又有 form

`401 Unauthorized` 缺少一个或多个 header

`400 Invalid TIMESTAMP` `TIMESTAMP` 无法解析

`425 TIMESTAMP is more than 60 seconds away from the server time` header 中的 `TIMESTAMP` 与服务器时间相差超过 60 秒

`401 Unknown APP_KEY` header 中的 `APP_KEY` 与 Flow 配置文件中的 `http_app_key` 不一致

`403 Forbidden` 签名校验失败

## 3. 设计规范

### 3.1 HTTP Method

- HTTP Method: 一律采用`POST`
- Content Type: application/json

### 3.2 URL规则(现有)

/一级/二级/N级/最后一级

- 一级：接口版本，如v1
- 二级：主资源名称，如job
- N级：子资源名称，如list, 允许有多个N级
- 最后一级：操作: create/update/query/get/delete

### 3.3 URL规则(建议改进)

/一级/二级/三级/四级/N级/最后一级

- 一级：系统名称: fate
- 三级：子系统名称: flow
- 二级：接口版本，如v1
- 四级：主资源名称，如job
- N级：子资源名称，如list, 允许有多个N级
- 最后一级：操作: create/update/query/get/delete
