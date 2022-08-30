# 认证方案

## 1. 说明

- 认证包含：客户端认证和站点认证

- 认证配置: `$FATE_BASE/conf/service_conf.yaml`：

  ```yaml
  # 站点鉴权时需要配置本方站点id
  party_id:
  # 钩子模块，需要根据不同场景配置不同的钩子
  hook_module:
    client_authentication: fate_flow.hook.flow.client_authentication
    site_authentication: fate_flow.hook.flow.site_authentication
  # 第三方认证服务名
  hook_server_name:
  authentication:
    client:
      # 客户端认证开关
      switch: false
      http_app_key:
      http_secret_key:
    site:
      # 站点认证开关
      switch: false
  ```
  
- 认证方式：支持flow自带的认证模块认证和第三方服务认证。可通过hook_module修改认证钩子，当前支持如下钩子：
  - client_authentication支持"fate_flow.hook.flow.client_authentication"和"fate_flow.hook.api.client_authentication", 其中前者是flow的客户端认证方式，后者是第三方服务客户端认证方式；
  - site_authentication支持"fate_flow.hook.flow.site_authentication"和"fate_flow.hook.api.site_authentication",其中前者是flow的站点端认证方式，后者是第三方服务站点认证方式。
	

## 2. 客户端认证

### 2.1 flow认证
#### 2.1.1 配置
`````yaml
hook_module:
  client_authentication: fate_flow.hook.flow.client_authentication
authentication:
  client:
    switch: true
    http_app_key: "xxx"
    http_secret_key: "xxx"
`````



#### 2.2.2 接口鉴权方式

则所有客户端发送到 Flow 的请求都需要增加以下 header

`TIMESTAMP`：Unix timestamp，单位毫秒，如 `1634890066095` 表示 `2021-10-22 16:07:46 GMT+0800`，注意该时间与服务器当前时间的差距不能超过 60 秒

`NONCE`：随机字符串，可以使用 UUID，如 `782d733e-330f-11ec-8be9-a0369fa972af`

`APP_KEY`：需与 Flow 配置文件中的 `http_app_key` 一致

`SIGNATURE`：基于 Flow 配置文件中的 `http_secret_key` 和请求参数生成的签名

#### 2.2.3 签名生成方法

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

#### 2.2.4 示例

可以参考 [Fate SDK](https://github.com/FederatedAI/FATE/blob/master/python/fate_client/flow_sdk/client/base.py#L63) 




### 2.2 第三方服务认证
#### 2.2.1 配置
```yaml
hook_module:
  client_authentication: fate_flow.hook.api.client_authentication
authentication:
  client:
    switch: true
hook_server_name: "xxx"
```

#### 2.2.2 接口鉴权方式
- 第三方服务需要向flow注册客户端认证接口，具体参考[客户端认证服务注册](./third_party_service_registry.zh.md#321-client_authentication)
- 若认证失败，flow会直接返回认证失败给客户端。

## 3. 站点认证

### 3.1 flow认证

#### 3.1.1 配置
```yaml
party_id: 9999
hook_module:
  site_authentication: fate_flow.hook.flow.site_authentication
authentication:
  client:
    switch: true
    http_app_key: "xxx"
    http_secret_key: "xxx"
```

#### 3.1.2 认证方案
- flow启动时会生成一对公钥和私钥，需要和合作方交换彼此的公钥，发送请求时通过RSA算法使用公钥生成签名，被请求站点通过其共钥验证签名。
- flow提供密钥管理cli，如下

#### 3.1.3 密钥管理
- 添加合作方公钥

{{snippet('cli/key.zh.md', '### save')}}

- 删除合作方公钥

{{snippet('cli/key.zh.md', '### delete')}}


- 查询共钥

{{snippet('cli/key.zh.md', '### query')}}

### 3.2 第三方服务认证
#### 3.2.1 配置
```yaml
hook_module:
  site_authentication: fate_flow.hook.api.site_authentication
authentication:
  site:
    switch: true
hook_server_name: "xxx"
```

#### 3.2.2 接口鉴权方式
- 第三方服务需要向flow注册站点认证接口，具体参考[站点认证服务注册](./third_party_service_registry.zh.md#3222-site_authentication)
- 若认证失败，flow会直接返回认证失败给发起方。