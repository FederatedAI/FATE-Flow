# Federated Model Registry

## 1. Description

Models trained by FATE are automatically saved locally and recorded in the FATE-Flow database. models saved after each component run are called Pipeline models, and models saved at regular intervals while the component is running are called Checkpoint models. checkpoint models can also be used for retrying after a component run is unexpectedly interrupted The Checkpoint model can also be used for "breakpoints" when a component is retrying after an unexpected interruption.

Checkpoint model support has been added since 1.7.0 and is not saved by default. To enable it, add the callback `ModelCheckpoint` to the DSL.

### Local disk storage

- Pipeline models are stored in `model_local_cache/<party_model_id>/<model_version>/variables/data/<component_name>/<model_alias>`.

- Checkpoint models are stored in `model_local_cache/<party_model_id>/<model_version>/checkpoint/<component_name>/<step_index>#<step_name>`.

### Remote storage engine

Local disk is not reliable, so there is a risk of losing models. FATE-Flow supports exporting models to specified storage engines, importing from specified storage engines, and pushing models to engine storage when publishing models automatically.

The storage engine supports Tencent Cloud Object Storage, MySQL and Redis, please refer to [Storage Engine Configuration](#4-storage-engine-configuration)

## 2. Model

{{snippet('cli/model.md', '## Model')}}

## 3. Checkpoint

{{snippet('cli/checkpoint.md', '## Checkpoint')}}

## 4. Storage engine configuration

### `enable_model_store`

This option affects API `/model/load`.

Automatic upload models to the model store if it exists locally but does not exist in the model storage, or download models from the model store if it does not exist locally but does not exist in the model storage.

This option does not affect API `/model/store` or `/model/restore`.

### `model_store_address`

This config defines which storage engine to use.

#### Tencent Cloud Object Storage

```yaml
storage: tencent_cos
# get these configs from Tencent Cloud console
Region:
SecretId:
SecretKey:
Bucket:
```

#### MySQL

```yaml
storage: mysql
database: fate_model
user: fate
password: fate
host: 127.0.0.1
port: 3306
# other optional configs send to the engine
max_connections: 10
stale_timeout: 10
```

#### Redis

```yaml
storage: redis
host: 127.0.0.1
port: 6379
db: 0
password:
# the expiry time of keys, in seconds. defaults None (no expiry time)
ex:
```
