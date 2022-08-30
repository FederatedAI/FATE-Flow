# 服务注册中心

## 1. 说明

### 1.1 模型注册

FATE-Flow 通过 Apache ZooKeeper 与 FATE-Serving 交互，如果在配置中启用了 `use_registry`，则 Flow 在启动时会向 ZooKeeper 注册模型的下载 URL，Serving 可以通过这些 URL 获取模型。

同样，Serving 也会向 ZooKeeper 注册其自身的地址，Flow 会获取该地址以与之通信。 如果没有启用 `use_registry`，Flow 则会尝试与配置文件中的设置 `servings` 地址通信。

### 1.2 高可用

FATE-Flow 通过向 Apache ZooKeeper 注册自身的 IP 和端口实现同一 party 内多节点的自动发现。

## 2. 配置 ZooKeeper 服务

```yaml
zookeeper:
  hosts:
    - 127.0.0.1:2181
  use_acl: false
  user: fate
  password: fate
```

## 3. ZNode

- FATE-Flow 模型注册: `/FATE-SERVICES/flow/online/transfer/providers`

- FATE-Flow 高可用: `/FATE-COMPONENTS/fate-flow`

- FATE-Serving: `/FATE-SERVICES/serving/online/publishLoad/providers`
