# Configuration Instructions

## 1. Description

Contains the general configuration of the `FATE project` and the configuration of each subsystem

## 2. Global configuration

- Path: `${FATE_PROJECT_BASE}/conf/server_conf.yaml`
- Description: Commonly used configuration, generally needed to determine when deploying
- Note: Configuration items that are not listed below in the configuration file are internal system parameters and are not recommended to be modified

```yaml
# If FATEFlow uses the registry, FATEFlow will register the FATEFlow Server address and the published model download address to the registry for the online system FATEServing; it will also get the FATEServing address from the registry.
use_registry: false
# Whether to enable higher security serialization mode
use_deserialize_safe_module: false
dependent_distribution: false
fateflow:
  # you must set real ip address, 127.0.0.1 and 0.0.0.0 is not supported
  host: 127.0.0.1
  http_port: 9380
  grpc_port: 9360
  http_app_key:
  http_secret_key:
  # support rollsite/nginx/fateflow as a coordination proxy
  # rollsite support fate on eggroll, use grpc protocol
  # nginx support fate on eggroll and fate on spark, use http or grpc protocol, default is http
  # fateflow support fate on eggroll and fate on spark, use http protocol, but not support exchange network mode

  # format(proxy: rollsite) means rollsite use the rollsite configuration of fate_one_eggroll and nginx use the nginx configuration of fate_one_spark
  # you also can customize the config like this(set fateflow of the opposite party as proxy):
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
# The registry address and its authentication parameters
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
    # CPU cores of the machine where eggroll nodemanager service is running
    cores_per_node: 16
    # the number of eggroll nodemanager machine
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
# default address for export model
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

# The address of the FATE Serving Server needs to be configured if the registry is not used
servings:
  hosts:
    - 127.0.0.1:8000
fatemanager:
  host: 127.0.0.1
  port: 8001
  federatedId: 0

```

## 3. FATE Flow Configuration

### 3.1 FATE Flow Server Configuration

- Path: `${FATE_FLOW_BASE}/python/fate_flow/settings.py`
- Description: Advanced configuration, generally no changes are needed
- Note: Configuration items that are not listed below in the configuration file are internal system parameters and are not recommended to be modified

```python
# Thread pool size of grpc server used by FATE Flow Server for multiparty FATE Flow Server communication, not set default equal to the number of CPU cores of the machine
GRPC_SERVER_MAX_WORKERS = None

# Switch
# The upload data interface gets data from the client by default, this value can be configured at the time of the interface call using use_local_data
UPLOAD_DATA_FROM_CLIENT = True
# Whether to enable multi-party communication authentication, need to be used with FATE Cloud
CHECK_NODES_IDENTITY = False
# Whether to enable the resource authentication function, need to use with FATE Cloud
USE_AUTHENTICATION = False
# Resource privileges granted by default
PRIVILEGE_COMMAND_WHITELIST = []
```

### 3.2 FATE Flow Default Job Configuration

- Path: `${FATE_FLOW_BASE}/conf/job_default_config.yaml`
- Description: Advanced configuration, generally no changes are needed
- Note: Configuration items that are not listed below in the configuration file are internal system parameters and are not recommended to be modified
- Take effect: use flow server reload or restart fate flow server

```yaml
# component provider, relative path to get_fate_python_directory
default_component_provider_path: federatedml

# resource
# total_cores_overweight_percent
total_cores_overweight_percent: 1 # 1 means no overweight
total_memory_overweight_percent: 1 # 1 means no overweight
# Default task parallelism per job, you can configure a custom value using job_parameters:task_parallelism when submitting the job configuration
task_parallelism: 1
# The default number of CPU cores per task per job, which can be configured using job_parameters:task_cores when submitting the job configuration
task_cores: 4
# This configuration does not take effect as memory resources are not supported for scheduling at the moment
task_memory: 0 # mb
# The ratio of the maximum number of CPU cores allowed for a job to the total number of resources, e.g., if the total resources are 10 and the value is 0.5, then a job is allowed to request up to 5 CPUs, i.e., task_cores * task_parallelism <= 10 * 0.5
max_cores_percent_per_job: 1 # 1 means total

# scheduling
# Default job execution timeout, you can configure a custom value using job_parameters:timeout when submitting the job configuration
job_timeout: 259200 # s
# Timeout for communication when sending cross-participant scheduling commands or status
remote_request_timeout: 30000 # ms
# Number of retries to send cross-participant scheduling commands or status
federated_command_trys: 3
end_status_job_scheduling_time_limit: 300000 # ms
end_status_job_scheduling_updates: 1
# Default number of auto retries, you can configure a custom value using job_parameters:auto_retries when submitting the job configuration
auto_retries: 0
# Default retry interval
auto_retry_delay: 1 #seconds
# Default multiparty status collection method, supports PULL and PUSH; you can also specify the current job collection mode in the job configuration
federated_status_collect_type: PUSH

# upload
upload_max_bytes: 104857600 # bytes

#component output
output_data_summary_count_limit: 100
```

## 4. FATE Board Configuration

- Path: `${FATE_BOARD_BASE}/conf/application.properties`
- Description: Commonly used configuration, generally needed to determine when deploying
- Note: Configuration items that are not listed below in the configuration file are internal system parameters and are not recommended to be modified

```properties
# Service listening port
server.port=8080
# fateflow address, referring to the http port address of fateflow
fateflow.url==http://127.0.0.1:9380
# db address, same as the above global configuration service_conf.yaml inside the database configuration
fateboard.datasource.jdbc-url=jdbc:mysql://localhost:3306/fate_flow?characterEncoding=utf8&characterSetResults=utf8&autoReconnect= true&failOverReadOnly=false&serverTimezone=GMT%2B8
# db configuration, same as the above global configuration service_conf.yaml inside the database configuration
fateboard.datasource.username=
# db configuration, same as the above global configuration service_conf.yaml inside the database configuration
fateboard.datasource.password=
server.tomcat.max-threads=1000
server.tomcat.max-connections=20000
spring.servlet.multipart.max-file-size=10MB
spring.servlet.multipart.max-request-size=100MB
# Administrator account configuration
server.board.login.username=admin
server.board.login.password=admin
server.ssl.key-store=classpath:
server.ssl.key-store-password=
server.ssl.key-password=
server.ssl.key-alias=
# When fateflo server enables api access authentication, you need to configure
HTTP_APP_KEY=
HTTP_SECRET_KEY=
```

## 5. EggRoll

### 5.1 System configuration

- Path: `${EGGROLL_HOME}/conf/eggroll.properties`
- Description: Commonly used configuration, generally needed to determine when deploying
- Note: Configuration items that are not listed below in the configuration file are internal system parameters and are not recommended to be modified

```properties
[eggroll]
# core
# MySQL connection configuration, generally required for production applications
eggroll.resourcemanager.clustermanager.jdbc.driver.class.name=com.mysql.cj.jdbc.
# MySQL connection configuration, generally required for production applications
eggroll.resourcemanager.clustermanager.jdbc.url=jdbc:mysql://localhost:3306/eggroll_meta?useSSL=false&serverTimezone=UTC& characterEncoding=utf8&allowPublicKeyRetrieval=true
# Connect to MySQL account, this configuration is required for general production applications
eggroll.resourcemanager.clustermanager.jdbc.username=
# Connect to MySQL password, generally required for production applications
eggroll.resourcemanager.clustermanager.jdbc.password=

# Data storage directory
eggroll.data.dir=data/
# Log storage directory
eggroll.logs.dir=logs/
eggroll.resourcemanager.clustermanager.host=127.0.0.1
eggroll.resourcemanager.clustermanager.port=4670
eggroll.resourcemanager.nodemanager.port=4670

# python path
eggroll.resourcemanager.bootstrap.eggg_pair.venv=
# pythonpath, usually you need to specify the python directory of eggroll and the python directory of fate
eggroll.resourcemanager.bootstrap.eggg_pair.pythonpath=python

# java path
eggroll.resourcemanager.bootstrap.eggg_frame.javahome=
# java service startup parameters, no special needs, no need to configure
eggroll.resourcemanager.bootstrap.eggg_frame.jvm.options=
# grpc connection hold time for multi-party communication
eggroll.core.grpc.channel.keepalive.timeout.sec=20

# session
# Number of computing processes started per nodemanager in an eggroll session; replaced by the default parameters of the fate flow if using fate for committing tasks
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

### 5.2 Routing table configuration

- Path: `${EGGROLL_HOME}/conf/route_table.json`
- Description: Commonly used configuration, generally needed to determine when deploying
  - The routing table is mainly divided into two levels
  - The first level indicates the site, if the corresponding target site configuration is not found, then use **default**
  - The second level represents the service, if you can not find the corresponding target service, then use **default**
  - The second level, usually set **default** as the address of our **rollsite** service, and **fateflow** as the grpc address of our **fate flow server** service

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
