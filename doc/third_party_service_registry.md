## Third party service registration center

## 1. Description
- fateflow supports third-party services for registration for callback scenarios
- All interfaces need to register the service address first, then register the interface

## 2. Registration
## 2.1 Server registration
- uri: ```/v1/server/<server_name>/register```
- Method: POST
- Request Parameters
    
| parameter name | required | type | description |
|:--------|:----|:-------|--------|
| host | yes | string | service ip address |
| port | yes | int | service port |

- Return parameters
    
| parameter name | type | description |
| :------ | :----- | -------- |
| retcode | int | return code |
| retmsg | string | return message |


## 2.2 Service Registration
- uri: ```/v1/service/registry```
- Method: POST
- Request Parameters 

| parameter name | required | type | description |
|:----|:-------|:------------|--------|
| server_name | yes | string | The name of the registered server |
| service_name | yes | string | service name |
| uri | yes | string | service uri |
| method | no | string | Request method, default "POST" |
| protocol | no | string | default "http" |

- Return parameters
    
| parameter name | type | description |
| :------ | :----- | -------- |
| retcode | int | return code |
| retmsg | string | Return information |


## 3 Interface parameter details
### 3.1 ApiReader
The ApiReader component requires third-party services to register three interfaces: upload, query, download, which are used to request feature data for offline ids.

#### 3.1.1 upload
- Description: upload interface passes the id to the third-party service
- Interface registration: refer to [service registration](#22-service-registration), where the service_name parameter is "upload".
- Request parameters
  - headers: {"Content-Type": "application/octet-stream"}
  - params: 
     
| parameter_name | required | type | description |
|:----|:---------|:-----------------|--------|
| requestBody | yes      | string | json string containing feature filtering parameters |
  - body: data stream

  - Example request (python).

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
- The interface returns:

| parameter name | type | description |
|:-------| :----- | -------- |
| code | int | return code |
| message | string | Returns the message |
| data | object | Returns the jobId parameter for asynchronous status queries |

#### 3.1.2 query
- Description: query interface is used to query the progress of a task.
- Interface registration: refer to [Service Registration](#22-service-registration), where the service_name parameter is "query".
- Request parameters
  - body
  
| parameter_name | mandatory | type | description |
|:----|:-------|:--------------|--------|
| jobId | yes | string | The jobId returned by upload |

- interface returns:

| parameter name | type | description |
|:-------|:-----| -------- |
| code | int | Return code |
| message | string | Return message |
| status | string | Task status |


#### 3.1.3 download
- Description: query interface for querying the progress of the task
- Interface registration: refer to [Service Registration](#22-service-registration), where the service_name parameter is "download".
- Request parameters
  - params

| parameter_name | mandatory | type | description |
|:----|:-------|:--------------|--------|
| requestBody | is | string | json string containing "jobId" |

- Interface Return: Feature data stream


### 3.2 Authentication
#### 3.2.1 Client authentication (client_authentication)
- Description: Client authentication is used to authenticate client requests
- Interface Registration: Refer to [Service Registration](#22-service-registration), where the service_name parameter is "client_authentication".
- Request parameters.
  - body

| parameter_name | required | type | description
|:----------|:----|:-------|------|
| full_path | yes | string | request path |
| headers | yes | string | request headers |
| form | no | object | request body |

- Interface Return: 

| parameter name | type | description |
|:-----|:-----| -------- |
| code | int | return code |
| msg | string | return message |


#### 3.2.2 Site Authentication
##### 3.2.2.1 signature
- Description: Before requesting another site, fate flow will call the signature interface to get the signature and put it in the request header
- Interface registration: Refer to [Service Registration](#22-service-registration), where the service_name parameter is "signature".
- Request parameters.
  - body

| parameter_name | mandatory | type | description |
|:---------|:----|:-------|------|
| party_id | yes | string | site id |
| body | yes | object | request body |


- Interface Return: 

| parameter name | type | description |
|:-----|:-----|-----|
| code | int | return code |
| site_signature | string | signature |

##### 3.2.2.2 site_authentication
- Description: Used to authenticate requests from other fate sites.
- Interface registration: refer to [Service Registration](#22-service-registration), where the service_name parameter is "site_authentication".
- Request parameters.
  - body

| parameter_name | required | type | description
|:---------------|:----|:-------|---------|
| src_party_id | yes | string | Requesting party site id |
| site_signature | yes | string | signature |
| body | yes | object | request body |

- Interface Return: 

| parameter name | type | description |
|:-----|:-----| -------- |
| code | int | return code |
| msg | string | return message |

### 3.3 permission
- Description: Authentication of requests from other sites
- Interface registration: refer to [service registration](#22-service-registration), where the service_name parameter is "permission".
- Request parameters
  - body

| parameter_name | mandatory | type | description
|:----------|:----|:-------|------|
| src_role | yes | string | Requesting party role |
| src_party_id | yes | string | Requesting party partyid |
| initiator | no | object | initiator information |
| roles | no | object | All participant information |
| component_list | yes | object | Component list |
| dataset_list | yes | object | dataset_list | yes | object
| run_time_conf | no | object | job conf |
| dsl | no | object | job dsl |
| component_parameters | no | object | component_parameters |


- interface returns: 

| parameter_name | type | description |
|:-----|:-----| -------- |
| code | int | return_code |
| msg | string | return message |