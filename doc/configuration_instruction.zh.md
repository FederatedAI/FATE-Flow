# 配置说明

## 1. 说明

包含`FATE项目`总配置以及各个子系统的配置

## 2. 全局配置

- 路径：`${FATE_PROJECT_BASE}/conf/server_conf.yaml`
- 说明：常用配置，一般部署时需要确定
- 注意：配置文件中未被列举如下的配置项属于系统内部参数，不建议修改

```yaml
# FATEFlow是否使用注册中心，使用注册中心的情况下，FATEFlow会注册FATEFlow Server地址以及发布的模型下载地址到注册中心以供在线系统FATEServing使用；同时也会从注册中心获取FATEServing地址
use_registry: false
# 是否启用更高安全级别的序列化模式
use_deserialize_safe_module: false
# fate on spark模式下是否启动依赖分发
dependent_distribution: false
# 是否启动密码加密(数据库密码)，开启后配置encrypt_module和private_key才生效
encrypt_password: false
# 加密包及加密函数(“#”号拼接)
encrypt_module: fate_arch.common.encrypt_utils#pwdecrypt
# 加密私钥
private_key:
fateflow:
  # 必须使用真实绑定的ip地址，避免因为多网卡/多IP引发的额外问题
  # you must set real ip address, 127.0.0.1 and 0.0.0.0 is not supported
  host: 127.0.0.1
  http_port: 9380
  grpc_port: 9360
  http_app_key:
  http_secret_key:
  # 支持使用rollsite/nginx/fateflow作为多方任务协调通信代理
  # rollsite支持fate on eggroll的场景，仅支持grpc协议，支持P2P组网及星型组网模式
  # nginx支持所有引擎场景，支持http与grpc协议，默认为http，支持P2P组网及星型组网模式
  # fateflow支持所有引擎场景，支持http与grpc协议，默认为http，仅支持P2P组网模式，也即只支持互相配置对端fateflow地址
  # 格式(proxy: rollsite)表示使用rollsite并使用下方fate_one_eggroll配置大类中的rollsite配置；配置nginx表示使用下方fate_one_spark配置大类中的nginx配置
  # 也可以直接配置对端fateflow的地址，如下所示：
  # proxy:
  #   name: fateflow
  #   host: xx
  #   http_port: xx
  #   grpc_port: xx
  proxy: rollsite
  # support default/http/grpc
  protocol: default
database:
  name: fate_flow
  user: fate
  passwd: fate
  host: 127.0.0.1
  port: 3306
  max_connections: 100
  stale_timeout: 30
# 注册中心地址及其身份认证参数
zookeeper:
  hosts:
    - 127.0.0.1:2181
  use_acl: false
  user: fate
  password: fate
# engine services
default_engines:
  computing: standalone
  federation: standalone
  storage: standalone
fate_on_standalone:
  standalone:
    cores_per_node: 20
    nodes: 1
fate_on_eggroll:
  clustermanager:
    # eggroll nodemanager服务所在机器的CPU核数
    cores_per_node: 16
    # eggroll nodemanager服务的机器数量
    nodes: 1
  rollsite:
    host: 127.0.0.1
    port: 9370
fate_on_spark:
  spark:
    # default use SPARK_HOME environment variable
    home:
    cores_per_node: 20
    nodes: 2
  linkis_spark:
    cores_per_node: 20
    nodes: 2
    host: 127.0.0.1
    port: 9001
    token_code: MLSS
    python_path: /data/projects/fate/python
  hive:
    host: 127.0.0.1
    port: 10000
    auth_mechanism:
    username:
    password:
  linkis_hive:
    host: 127.0.0.1
    port: 9001
  hdfs:
    name_node: hdfs://fate-cluster
    # default /
    path_prefix:
  rabbitmq:
    host: 192.168.0.4
    mng_port: 12345
    port: 5672
    user: fate
    password: fate
    # default conf/rabbitmq_route_table.yaml
    route_table:
  pulsar:
    host: 192.168.0.5
    port: 6650
    mng_port: 8080
    cluster: standalone
    # all parties should use a same tenant
    tenant: fl-tenant
    # message ttl in minutes
    topic_ttl: 5
    # default conf/pulsar_route_table.yaml
    route_table:
  nginx:
    host: 127.0.0.1
    http_port: 9300
    grpc_port: 9310
# external services
fateboard:
  host: 127.0.0.1
  port: 8080

# on API `/model/load` and `/model/load/do`
# automatic upload models to the model store if it exists locally but does not exist in the model storage
# or download models from the model store if it does not exist locally but exists in the model storage
# this config will not affect API `/model/store` or `/model/restore`
enable_model_store: false
# 模型导出(export model)操作默认的导出地址
model_store_address:
  # use mysql as the model store engine
#  storage: mysql
#  database: fate_model
#  user: fate
#  password: fate
#  host: 127.0.0.1
#  port: 3306
  # other optional configs send to the engine
#  max_connections: 10
#  stale_timeout: 10
  # use redis as the model store engine
#  storage: redis
#  host: 127.0.0.1
#  port: 6379
#  db: 0
#  password:
  # the expiry time of keys, in seconds. defaults None (no expiry time)
#  ex:
  # use tencent cos as model store engine
  storage: tencent_cos
  Region:
  SecretId:
  SecretKey:
  Bucket:

# 不使用注册中心的情况下，需要配置FATE Serving Server的地址
servings:
  hosts:
    - 127.0.0.1:8000
fatemanager:
  host: 127.0.0.1
  port: 8001
  federatedId: 0

```

## 3. FATE Flow配置

### 3.1 FATE Flow Server配置

- 路径：`${FATE_FLOW_BASE}/python/fate_flow/settings.py`
- 说明：高级配置，一般不需要做改动
- 注意：配置文件中未被列举如下的配置项属于系统内部参数，不建议修改

```python
# FATE Flow Server用于多方FATE Flow Server通信的grpc server的线程池大小，不设置默认等于机器CPU核数
GRPC_SERVER_MAX_WORKERS = None

# Switch
# 上传数据接口默认从客户端获取数据，该值可以在接口调用时使用use_local_data配置自定义值
UPLOAD_DATA_FROM_CLIENT = True
# 是否开启多方通信身份认证功能，需要配合FATE Cloud使用
CHECK_NODES_IDENTITY = False
# 是否开启资源鉴权功能，需要配合FATE Cloud使用
USE_AUTHENTICATION = False
# 默认授予的资源权限
PRIVILEGE_COMMAND_WHITELIST = []
```

### 3.2 FATE Flow 默认作业配置

- 路径：`${FATE_FLOW_BASE}/conf/job_default_config.yaml`
- 说明：高级配置，一般不需要做改动
- 注意：配置文件中未被列举如下的配置项属于系统内部参数，不建议修改
- 生效：使用flow server reload或者重启fate flow server

```yaml
# component provider, relative path to get_fate_python_directory
default_component_provider_path: federatedml

# resource
# 总资源超配百分比
total_cores_overweight_percent: 1  # 1 means no overweight
total_memory_overweight_percent: 1  # 1 means no overweight
# 默认的每个作业的任务并行度，可以在提交作业配置时使用job_parameters:task_parallelism配置自定义值
task_parallelism: 1
# 默认的每个作业中每个任务使用的CPU核数，可以在提交作业配置时使用job_parameters:task_cores配置自定义值
task_cores: 4
# 暂时不支持内存资源的调度，该配置不生效
task_memory: 0  # mb
# 一个作业最大允许申请的CPU核数占总资源数量的比例，如总资源为10，此值为0.5，则表示一个作业最多允许申请5个CPU，也即task_cores * task_parallelism <= 10 * 0.5
max_cores_percent_per_job: 1  # 1 means total

# scheduling
# 默认的作业执行超时时间，可以在提交作业配置时使用job_parameters:timeout配置自定义值
job_timeout: 259200 # s
# 发送跨参与方调度命令或者状态时，通信的超时时间
remote_request_timeout: 30000  # ms
# 发送跨参与方调度命令或者状态时，通信的重试次数
federated_command_trys: 3
end_status_job_scheduling_time_limit: 300000 # ms
end_status_job_scheduling_updates: 1
# 默认自动重试次数, 可以在提交作业配置时使用job_parameters:auto_retries配置自定义值
auto_retries: 0
# 默认重试次数间隔
auto_retry_delay: 1  #seconds
# 默认的多方状态收集方式，支持PULL和PUSH；也可在作业配置指定当前作业的收集模式
federated_status_collect_type: PUSH

# upload
upload_max_bytes: 104857600 # bytes

#component output
output_data_summary_count_limit: 100
```

## 4. FATE Board配置

- 路径：`${FATE_BOARD_BASE}/conf/application.properties`
- 说明：常用配置，一般部署时需要确定
- 注意：配置文件中未被列举如下的配置项属于系统内部参数，不建议修改

```properties
# 服务监听端口
server.port=8080
# fateflow地址，指fateflow的http端口地址
fateflow.url==http://127.0.0.1:9380
# db地址，同上述全局配置service_conf.yaml里面的database配置
fateboard.datasource.jdbc-url=jdbc:mysql://localhost:3306/fate_flow?characterEncoding=utf8&characterSetResults=utf8&autoReconnect=true&failOverReadOnly=false&serverTimezone=GMT%2B8
# db配置，同上述全局配置service_conf.yaml里面的database配置
fateboard.datasource.username=
# db配置，同上述全局配置service_conf.yaml里面的database配置
fateboard.datasource.password=
server.tomcat.max-threads=1000
server.tomcat.max-connections=20000
spring.servlet.multipart.max-file-size=10MB
spring.servlet.multipart.max-request-size=100MB
# 管理员账号配置
server.board.login.username=admin
server.board.login.password=admin
server.ssl.key-store=classpath:
server.ssl.key-store-password=
server.ssl.key-password=
server.ssl.key-alias=
# 当fateflo server开启api访问鉴权时，需要配置
HTTP_APP_KEY=
HTTP_SECRET_KEY=
```

## 5. EggRoll

### 5.1 系统配置

- 路径：`${EGGROLL_HOME}/conf/eggroll.properties`
- 说明：常用配置，一般部署时需要确定
- 注意：配置文件中未被列举如下的配置项属于系统内部参数，不建议修改

```properties
[eggroll]
# core
# 连接MySQL配置，一般生产应用需要此配置
eggroll.resourcemanager.clustermanager.jdbc.driver.class.name=com.mysql.cj.jdbc.Driver
# 连接MySQL配置，一般生产应用需要此配置
eggroll.resourcemanager.clustermanager.jdbc.url=jdbc:mysql://localhost:3306/eggroll_meta?useSSL=false&serverTimezone=UTC&characterEncoding=utf8&allowPublicKeyRetrieval=true
# 连接MySQL账户，一般生产应用需要此配置
eggroll.resourcemanager.clustermanager.jdbc.username=
# 连接MySQL密码，一般生产应用需要此配置
eggroll.resourcemanager.clustermanager.jdbc.password=

# 数据存储目录
eggroll.data.dir=data/
# 日志存储目录
eggroll.logs.dir=logs/
eggroll.resourcemanager.clustermanager.host=127.0.0.1
eggroll.resourcemanager.clustermanager.port=4670
eggroll.resourcemanager.nodemanager.port=4670

# python路径
eggroll.resourcemanager.bootstrap.egg_pair.venv=
# pythonpath, 一般需要指定eggroll的python目录以及fate的python目录
eggroll.resourcemanager.bootstrap.egg_pair.pythonpath=python

# java路径
eggroll.resourcemanager.bootstrap.egg_frame.javahome=
# java服务启动参数，无特别需要，无需配置
eggroll.resourcemanager.bootstrap.egg_frame.jvm.options=
# 多方通信时，grpc连接保持时间
eggroll.core.grpc.channel.keepalive.timeout.sec=20

# session
# 一个eggroll会话中，每个nodemanager启动的计算进程数量;若使用fate进行提交任务，则会被fate flow的默认参数所代替
eggroll.session.processors.per.node=4

# rollsite
eggroll.rollsite.coordinator=webank
eggroll.rollsite.host=127.0.0.1
eggroll.rollsite.port=9370
eggroll.rollsite.party.id=10001
eggroll.rollsite.route.table.path=conf/route_table.json

eggroll.rollsite.push.max.retry=3
eggroll.rollsite.push.long.retry=2
eggroll.rollsite.push.batches.per.stream=10
eggroll.rollsite.adapter.sendbuf.size=100000
```

### 5.2 路由表配置

- 路径：`${EGGROLL_HOME}/conf/route_table.json`
- 说明：常用配置，一般部署时需要确定 
  - 路由表主要分两个层级表示
  - 第一级表示站点，若找不到对应的目标站点配置，则使用**default**
  - 第二级表示服务，若找不到对应的目标服务，则使用**default**
  - 第二级，通常将**default**设为本方**rollsite**服务地址，将**fateflow**设为本方**fate flow server**服务的grpc地址

```json
{
  "route_table":
  {
    "10001":
    {
      "default":[
        {
          "port": 9370,
          "ip": "127.0.0.1"
        }
      ],
      "fateflow":[
        {
          "port": 9360,
          "ip": "127.0.0.1"
        }
      ]
    },
    "10002":
    {
      "default":[
        {
          "port": 9470,
          "ip": "127.0.0.1"
        }
      ]
    }
  },
  "permission":
  {
    "default_allow": true
  }
}
```