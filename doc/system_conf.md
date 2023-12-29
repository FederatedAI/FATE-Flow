# System Configuration
FATE Flow uses YAML to define system configurations, and the configuration file is located at: `conf/service_conf.yaml`. The specific configuration contents and their meanings are as follows:

| Configuration Item | Description                                                                                                                                                                                                      | Values                                                                                        |
|--------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------|
| party_id           | Local site ID                                                                                                                                                                                                    | For example, "9999", "10000"                                                                  |
| log_level          | Log level                                                                                                                                                                                                        | DEBUG:10, INFO:20, DEBUG:30, ERROR: 40                                                        |
| use_registry       | Whether to use a registry center; currently, only ZooKeeper mode is supported, and it requires correct ZooKeeper configuration. Note: If using high availability mode, ensure this configuration is set to true. | true/false                                                                                    |
| encrypt            | Encryption module                                                                                                                                                                                                | See [Encryption Module](#encryption-module)                                                   |
| fateflow           | Configuration for the FATE Flow service, including ports, command channel service, and proxy                                                                                                                     | See [FateFlow Configuration](#fateflow-configuration)                                         |
| database           | Configuration information for the database service                                                                                                                                                               | See [Database Configuration](#database-configuration)                                         |
| default_engines    | System's engine services, including computing, storage, and communication engines                                                                                                                                | See [Engine Configuration](#engine-configuration)                                             |
| default_provider   | Component source information, including provider name, component version, and execution mode                                                                                                                     | See [Default Registered Algorithm Configuration](#default-registered-algorithm-configuration) |
| federation         | Communication service pool                                                                                                                                                                                       | See [Communication Engine Pool](#communication-engine-pool)                                   |
| computing          | Computing service pool                                                                                                                                                                                           | See [Computing Engine Pool](#computing-engine-pool)                                           |
| storage            | Storage service pool                                                                                                                                                                                             | See [Storage Engine Pool](#storage-configuration)                                             |
| hook_module        | Hook configuration, currently supports client authentication, site authentication, and authorization hooks                                                                                                       | See [Hook Module Configuration](#hook-module-configuration)                                   |
| authentication     | Authentication and authorization switches                                                                                                                                                                        | See [Authentication Switch](#authentication-switch)                                           |
| model_store        | Model storage configuration                                                                                                                                                                                      | See [Model Storage](#model-storage)                                                           |
| zookeeper          | ZooKeeper service configuration                                                                                                                                                                                  | See [ZooKeeper Configuration](#zookeeper-configuration)                                       |

## Encryption Module
```yaml
key_0:
  module: fate_flow.hub.encrypt.password_encrypt#pwdecrypt
  private_path: private_key.pem
```
This encryption module is primarily used for encrypting passwords (e.g., MySQL passwords):
- "key_0" is the key for the encryption module (you can customize the name), making it easier to reference in other configurations when multiple encryption modes coexist.
  - module: The encryption module, formatted as "encryption module" + "#" + "encryption function."
  - private_path: The path to the encryption key. If you provide a relative path, its root directory is `fate_flow/conf/`.

## FateFlow Configuration
```yaml
host: 127.0.0.1
http_port: 9380
grpc_port: 9360
proxy_name: osx
nginx:
  host:
  http_port:
  grpc_port:
```
- host: Host address.
- http_port: HTTP port number.
- grpc_port: gRPC port number.
- proxy_name: Command channel service name, supporting osx/nginx. Detailed configurations need to be set within [Communication Engine Pool](#communication-engine-pool).
- nginx: Proxy service configuration for load balancing.

## Database Configuration
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
- engine: Database engine name. If set to "mysql" here, update the detailed MySQL configuration.
- decrypt_key: Encryption module, selected from [Encryption Module](#encryption-module). If not configured, it's considered to not use password encryption. If used, you need to set the "passwd" below to ciphertext and configure the key path in [Encryption Module](#encryption-module).
- mysql: MySQL service configuration. If using password encryption functionality, set the "passwd" in this configuration to ciphertext and configure the key path in [Encryption Module](#encryption-module).
- sqlite: SQLite file path, default path is `fate_flow/fate_flow_sqlite.db`.

## Engine Configuration
```yaml
default_engines:
  computing: standalone
  federation: standalone
  storage: standalone
```

- computing: Computing engine, supports "standalone", "eggroll", "spark".
- federation: Communication engine, supports "standalone", "osx", "rabbitmq", "pulsar".
- storage: Storage engine, supports "standalone," "eggroll," "hdfs."

## Default Registered Algorithm Configuration
- name: Algorithm name.
- version: Algorithm version. If not configured, it uses the configuration in `fateflow.env`.
- device: Algorithm launch mode, local/docker/k8s, etc.

## Communication Engine Pool

### OSx
```yaml
  host: 127.0.0.1
  port: 9370
  mode: stream
```

## Computing Engine Pool
### Standalone
```yaml
  cores: 32
```
- cores: Total resources.

### Eggroll
```yaml
eggroll:
  cores: 32
  nodes: 1
  host: 127.0.0.1
  port: 4670
```
- cores: Total cluster resources.
- nodes: Number of node managers in the cluster.
- host: eggroll cluster manager host ip
- port: eggroll cluster manager port

### Spark
```yaml
spark:
  home: 
  cores: 32
```
- home: Spark home directory. If not filled, "pyspark" will be used as the computing engine.
- cores: Total resources.

## Storage Engine Pool
```yaml
  hdfs:
    name_node: hdfs://fate-cluster
```

## Hook Module Configuration
```yaml
hook_module:
  client_authentication: fate_flow.hook.flow.client_authentication
  site_authentication: fate_flow.hook.flow.site_authentication
  permission: fate_flow.hook.flow.permission
```
- client_authentication: Client authentication hook.
- site_authentication: Site authentication hook.
- permission: Permission authentication hook.

## Authentication Switch
```yaml
authentication:
  client: false
  site: false
  permission: false
```

## Model Storage
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
- engine: Model storage engine, supports "file," "mysql", and "tencent_cos".
- decrypt_key: Encryption module, needs to be selected from [Encryption Module](#encryption-module). If not configured, it is assumed to not use password encryption. If used, you need to set the "passwd" below accordingly to ciphertext and configure the key path in [Encryption Module](#encryption-module).
- file: Model storage directory, default location is `fate_flow/model`.
- mysql: MySQL service configuration; if using password encryption functionality, you need to set the "passwd" in this configuration to ciphertext and configure the key path in [Encryption Module](#encryption-module).
- tencent_cos: Tencent Cloud key configuration.

## ZooKeeper Configuration
```yaml
zookeeper:
  hosts:
    - 127.0.0.1:2181
  use_acl: true
  user: fate
  password: fate
```