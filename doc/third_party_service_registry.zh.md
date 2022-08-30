# 第三方服务注册中心

## 1. 说明
- fateflow支持第三方服务进行注册，用于回调场景
- 所有的接口需要先注册服务地址，再注册接口

## 2. 注册
### 2.1 服务器注册
- uri: ```/v1/server/<server_name>/register```
- 方式：POST
- 请求参数
    
| 参数名     | 必选  | 类型     | 说明     |
|:--------|:----|:-------|--------|
| host    | 是   | string | 服务ip地址 |
| port    | 是   | int    | 服务端口   |

- 返回参数
    
| 参数名  | 类型   | 说明     |
| :------ | :----- | -------- |
| retcode | int    | 返回码   |
| retmsg  | string | 返回信息 |


## 2.2 服务注册
- uri: ```/v1/service/registry```
- 方式：POST
- 请求参数 

| 参数名          | 必选  | 类型     | 说明          |
|:----|:-------|:------------|--------|
| server_name  | 是   | string | 注册的服务器名字    |
| service_name | 是   | string | 服务名         |
| uri            | 是   | string | 服务uri       |
| method            | 否   | string | 请求方式，默认"POST" |
| protocol            | 否   | string | 默认"http"    |

- 返回参数
    
| 参数名  | 类型   | 说明     |
| :------ | :----- | -------- |
| retcode | int    | 返回码   |
| retmsg  | string | 返回信息 |


## 3 接口参数详情
### 3.1 ApiReader
ApiReader组件需要第三方服务注册三个接口：upload、query、download，用于请求离线id的特征数据。

#### 3.1.1 upload
- 说明：upload接口将id传给第三方服务
- 接口注册：参考[服务注册](#2-服务注册)，其中service_name参数为"upload"
- 请求参数：
  - headers: {"Content-Type": "application/octet-stream"}
  - params: 
     
| 参数名          | 必选  | 类型     | 说明               |
|:----|:-------|:-----------------|--------|
| requestBody  | 是   | string | json字符串，包含特征筛选参数 |
  - body：数据流

  - 请求示例(python)：

      ```python
        
      with open(id_path, "w") as f:
          data = MultipartEncoder(
              fields={'file': (id_path, f, 'application/octet-stream')}
          )
          upload_registry_info = service_info.get("upload")
          response = getattr(requests, upload_registry_info.f_method.lower(), None)(
              url=upload_registry_info.f_url,
              params={"requestBody": json.dumps({"stat_month": "202201", "version": "v1"})},
              data=data,
              headers={'Content-Type': "application/octet-stream"}
          )
      ```
- 接口返回:

| 参数名     | 类型     | 说明     |
|:-------| :----- | -------- |
| code    | int    | 返回码   |
| message | string | 返回信息 |
| data    | object | 返回参数jobId，用于异步状态查询 |

#### 3.1.2 query
- 说明：query接口用于查询任务进度
- 接口注册：参考[服务注册](#2-服务注册)，其中service_name参数为"query"
- 请求参数：
  - body：
  
| 参数名          | 必选  | 类型     | 说明            |
|:----|:-------|:--------------|--------|
| jobId  | 是   | string | upload返回的jobId |

- 接口返回:

| 参数名  | 类型     | 说明   |
|:-------|:-----| -------- |
| code | int    | 返回码  |
| message | string | 返回信息 |
| status    | string | 任务状态 |


#### 3.1.3 download
- 说明：query接口用于查询任务进度
- 接口注册：参考[服务注册](#2-服务注册)，其中service_name参数为"download"
- 请求参数：
  - params：

| 参数名          | 必选  | 类型     | 说明            |
|:----|:-------|:--------------|--------|
| requestBody  | 是   | string | json字符串，包含"jobId" |

- 接口返回: 特征数据流


### 3.2 认证
#### 3.2.1 客户端认证(client_authentication)
- 说明：客户端认证用于认证客户端的请求
- 接口注册：参考[服务注册](#2-服务注册)，其中service_name参数为"client_authentication"
- 请求参数：
  - body：

| 参数名       | 必选  | 类型     | 说明   |
|:----------|:----|:-------|------|
| full_path | 是   | string | 请求路径 |
| headers   | 是   | string | 请求头  |
| form      | 否   | object | 请求体  |

- 接口返回: 

| 参数名  | 类型     | 说明   |
|:-----|:-----| -------- |
| code | int    | 返回码  |
| msg  | string | 返回信息 |


#### 3.2.2 站点认证
##### 3.2.2.1 signature
- 说明：请求其他站点前，fate flow会调用签名接口获取签名并放到请求头中
- 接口注册：参考[服务注册](#2-服务注册)，其中service_name参数为"signature"
- 请求参数：
  - body：

| 参数名      | 必选  | 类型     | 说明   |
|:---------|:----|:-------|------|
| party_id | 是   | string | 站点id |
| body     | 是   | object | 请求体  |


- 接口返回: 

| 参数名  | 类型     | 说明  |
|:-----|:-----|-----|
| code | int    | 返回码 |
| site_signature  | string | 签名 |

##### 3.2.2.2 site_authentication
- 说明：用于认证其他fate站点的请求
- 接口注册：参考[服务注册](#2-服务注册)，其中service_name参数为"site_authentication"
- 请求参数：
  - body：

| 参数名            | 必选  | 类型     | 说明      |
|:---------------|:----|:-------|---------|
| src_party_id   | 是   | string | 请求方站点id |
| site_signature | 是   | string | 签名      |
| body           | 是   | object | 请求体     |

- 接口返回: 

| 参数名  | 类型     | 说明   |
|:-----|:-----| -------- |
| code | int    | 返回码  |
| msg  | string | 返回信息 |

### 3.3 鉴权(permission)
- 说明：对其他站点的请求进行鉴权
- 接口注册：参考[服务注册](#2-服务注册)，其中service_name参数为"permission"
- 请求参数：
  - body：

| 参数名       | 必选  | 类型     | 说明   |
|:----------|:----|:-------|------|
| src_role | 是   | string | 请求方角色 |
| src_party_id   | 是   | string | 请求方partyid |
| initiator      | 否   | object | 发起方信息 |
| roles      | 否   | object | 全部参与方信息 |
| component_list      | 是   | object | 组件列表 |
| dataset_list      | 是   | object | 数据集列表 |
| run_time_conf      | 否   | object | job conf |
| dsl      | 否   | object | job dsl |
| component_parameters      | 否   | object | 组件参数 |


- 接口返回: 

| 参数名  | 类型     | 说明   |
|:-----|:-----| -------- |
| code | int    | 返回码  |
| msg  | string | 返回信息 |