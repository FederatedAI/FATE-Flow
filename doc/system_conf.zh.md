# 系统配置描述文档
FATE Flow使用yaml定义系统配置，配置路径位于: conf/service_conf.yaml, 具体配置内容及其含义如下：

| 配置项              | 说明 | 值                            |
|----------------------|------|------------------------------|
| party_id             | 本方站点id | 如: "9999", "10000            |
| use_registry         | 是否使用注册中心，当前仅支持zookeeper模式，需要保证zookeeper的配置正确；<br/>注：若使用高可用模式，需保证该配置设置为true | true/false                   |
| encrypt              | 加密模块 | 见[加密模块](#加密模块)               |
| fateflow             | FATE Flow服务的配置，主要包括端口、命令通道服务、代理等 | 见[FateFlow配置](#fateflow配置)   |
| database             | 数据库服务的配置信息 | 见[数据库配置](#数据库配置)             |
| default_engines      | 系统的引擎服务，主要包括计算、存储和通信引擎 | 见[引擎配置](#引擎配置)               |
| default_provider     | 组件的来源信息，主要包括提供方名称、组件版本和运行模式 | 见[默认注册算法配置](#默认注册算法配置)               |
| federation           | 通信服务池 | 见[通信引擎池](#通信引擎池)             |
| computing            | 计算服务池 | 见[计算引擎池](#计算引擎池)             |
| storage              | 存储服务池 | 见[存储引擎池](#存储配置)              |
| hook_module          | 钩子配置，当前支持客户端认证、站点端认证以及鉴权钩子 | 见[钩子模块配置](#钩子模块配置)           |
| authentication       | 认证&&鉴权开关 | 见[认证开关](#认证开关)               |
| model_store          | 模型存储配置 | 见[模型存储](#模型存储)               |
| zookeeper            | zookeeper服务的配置 | 见[zookeeper配置](#zookeeper配置) |

## 加密模块
```yaml
key_0:
  module: fate_flow.hub.encrypt.password_encrypt#pwdecrypt
  private_path: private_key.pem
```
该加密模块主要用于密码(如mysql密码)等内容加密：
- 其中"key_0"为加密模块的key(可以自定义名字)，便于其它配置中直接引用，多套加密模式共存。
  - module: 加密模块，拼接规则为：加密模块 + "#" + 加密函数。
  - private_path：密钥路径。如填相对路径，其根目录位于fate_flow/conf/

## FateFlow配置
```yaml
host: 127.0.0.1
http_port: 9380
grpc_port: 9360
proxy_name: rollsite
nginx:
  host:
  http_port:
  grpc_port:
```
- host: 主机地址;
- http_port：http端口号;
- grpc_port: grpc端口号;
- proxy_name: 命令通道服务名，支持osx/rollsite/nginx。详细配置需要在[通信引擎池](#通信引擎池) 里面配置;
- nginx: 代理服务配置，用于负载均衡。

## 数据库配置
```yaml
engine: sqlite
decrypt_key:
mysql:
  name: fate_flow
  user: fate
  passwd: fate
  host: 127.0.0.1
  port: 3306
  max_connections: 100
  stale_timeout: 30
sqlite:
  path:
```
- engine: 数据库引擎名字，如这里填"mysql"，则需要更新mysql的配置详细配置。
- decrypt_key: 加密模块,需要从[加密模块](#加密模块)中选择。 若不配置，视为不使用密码加密；若使用，则需要将下面的passwd相应设置为密文。
- mysql: mysql服务配置；若使用密码加密功能，需要将此配置中的"passwd"设置为密文，并在[加密模块](#加密模块)中配置密钥路径
- sqlite: sqlite文件路径，默认路径为fate_flow/fate_flow_sqlite.db

## 引擎配置
```yaml
default_engines:
  computing: standalone
  federation: standalone
  storage: standalone
```

- computing: 计算引擎，支持"standalone"、"eggroll"、"spark"
- federation: 通信引擎，支持"standalone"、"rollsite"、"osx"、"rabbitmq"、"pulsar"
- storage: 存储引擎，支持"standalone"、"eggroll"、"hdfs"

## 默认注册算法配置
- name: 算法名称
- version: 算法版本，若不配置，则使用fateflow.env中的配置
- device: 算法启动方式, local/docker/k8s等

## 通信引擎池
### pulsar
```yaml
pulsar:
  host: 192.168.0.5
  port: 6650
  mng_port: 8080
  cluster: standalone
  tenant: fl-tenant
  topic_ttl: 30
  # default conf/pulsar_route_table.yaml
  route_table:
  # mode: replication / client, default: replication
  mode: replication
  max_message_size: 1048576
```
### nginx:
```yaml
nginx:
  host: 127.0.0.1
  http_port: 9300
  grpc_port: 9310
  # http or grpc
  protocol: http
```

### rabbitmq
```yaml
nginx:
  host: 127.0.0.1
  http_port: 9300
  grpc_port: 9310
  # http or grpc
  protocol: http
```

### rollsite
```yaml
rollsite:
  host: 127.0.0.1
  port: 9370
```

### osx
```yaml
  host: 127.0.0.1
  port: 9370
```

## 计算引擎池
### standalone
```yaml
  cores: 32
```
- cores: 资源总数

### eggroll
```yaml
eggroll:
  cores: 32
  nodes: 2
```
- cores: 集群资源总数
- nodes: 集群node-manager数量

### spark
```yaml
eggroll:
  home: 
  cores: 32
```
- home: spark home目录，如果不填，将使用"pyspark"作为计算引擎。
- cores: 资源总数

## 存储引擎池
```yaml
  hdfs:
    name_node: hdfs://fate-cluster
```

## 钩子模块配置
```yaml
hook_module:
  client_authentication: fate_flow.hook.flow.client_authentication
  site_authentication: fate_flow.hook.flow.site_authentication
  permission: fate_flow.hook.flow.permission
```
- client_authentication: 客户端认证钩子
- site_authentication: 站点认证钩子
- permission: 权限认证钩子

## 认证开关
```yaml
authentication:
  client: false
  site: false
  permission: false
```

## 模型存储
```yaml
model_store:
  engine: file
  decrypt_key:
  file:
    path:
  mysql:
    name: fate_flow
    user: fate
    passwd: fate
    host: 127.0.0.1
    port: 3306
    max_connections: 100
    stale_timeout: 30
  tencent_cos:
    Region:
    SecretId:
    SecretKey:
    Bucket:
```
- engine: 模型存储引擎，支持"file"、"mysql"和"tencent_cos"。
- decrypt_key: 加密模块,需要从[加密模块](#加密模块)中选择。 若不配置，视为不使用密码加密；若使用，则需要将下面的passwd相应设置为密文。
- file: 模型存储目录，默认位于： fate_flow/model
- mysql: mysql服务配置；若使用密码加密功能，需要将此配置中的"passwd"设置为密文，并在[加密模块](#加密模块)中配置密钥路径
- tencent_cos: 腾讯云密钥配置


## zookeeper配置
```yaml
zookeeper:
  hosts:
    - 127.0.0.1:2181
  use_acl: true
  user: fate
  password: fate
```