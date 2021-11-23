# Service Registry

## 1. Description

FATE-Flow interacts with FATE-Serving through Apache ZooKeeper. If `use_registry` is enabled in the configuration, Flow registers model download URLs with ZooKeeper when it starts, and Serving can get the models through these URLs.

Likewise, Serving registers its own address with ZooKeeper, which Flow will fetch to communicate with. If `use_registry` is not enabled, Flow will try to communicate with the set `servings` address in the configuration file.

## 2. Configuring the ZooKeeper service

```yaml
zookeeper:
  hosts:
    - 127.0.0.1:2181
  use_acl: false
  user: fate
  password: fate
```

## 3. ZNode

- FATE-Flow: `/FATE-SERVICES/flow/online/transfer/providers`

- FATE-Serving: `/FATE-SERVICES/serving/online/publishLoad/providers`
